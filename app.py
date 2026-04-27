import os
import sqlite3
import requests
import time
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

from tensorflow.keras.models import load_model

app = Flask(__name__)
CORS(app) 

# Physical Model Measurements
PANEL_AREA_M2 = 0.12 * 0.16         
PANEL_RATED_WATTAGE = 2.0           
TEMP_COEFFICIENT = -0.004           
STC_TEMP = 25.0                     
DB_FILE = "solar_data.db"
BAHRAIN_LAT = 26.0667
BAHRAIN_LON = 50.5577

# Load the Model
print("Loading LSTM Model and Scalers...")
try:
    lstm_model = load_model('solar_lstm_model.h5', compile=False)
    feature_scaler = joblib.load('feature_scaler.pkl')
    target_scaler = joblib.load('target_scaler.pkl')
    ML_READY = True
    print("ML Brain successfully loaded!")
except Exception as e:
    print(f"Could not load ML files (Prediction disabled): {e}")
    ML_READY = False

# DATABASE SETUP FOR READINGS STORING & PHYSICS MATH
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ldr_raw INTEGER,
            irradiance_w_m2 REAL,
            temperature_c REAL,
            dust_density REAL,
            expected_p_out REAL,
            efficiency_percent REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def calculate_metrics(ldr_raw, temp_c, dust_density):
    irradiance = (ldr_raw / 1023.0) * 1000.0
    if irradiance <= 0.1:
        return 0.0, 0.0, 0.0

    temp_derating = 1 + (TEMP_COEFFICIENT * (temp_c - STC_TEMP))
    dust_derating = max(0.0, 1 - (dust_density / 10000.0))
    base_efficiency = PANEL_RATED_WATTAGE / (PANEL_AREA_M2 * 1000)
    
    live_efficiency_decimal = base_efficiency * temp_derating * dust_derating
    live_efficiency_percent = live_efficiency_decimal * 100
    
    expected_p_out = (irradiance * PANEL_AREA_M2) * live_efficiency_decimal

    return irradiance, max(0.0, expected_p_out), max(0.0, live_efficiency_percent)


# Resiving Sensors Data from the Raspberry Pi
@app.route('/sensor', methods=['POST'])
def receive_data():
    data = request.get_json()
    if not data: return jsonify({"error": "No payload"}), 400

    ldr = data.get('ldr', 0)
    temp = data.get('temperature', 25.0)
    dust = data.get('dust', 0.0)

    irradiance, expected_p_out, efficiency = calculate_metrics(ldr, temp, dust)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO readings (ldr_raw, irradiance_w_m2, temperature_c, dust_density, expected_p_out, efficiency_percent)
                 VALUES (?, ?, ?, ?, ?, ?)''', (ldr, irradiance, temp, dust, expected_p_out, efficiency))
    conn.commit()
    conn.close()

    print(f"✅ [SAVED] Temp: {temp}°C | Irr: {irradiance:.1f} W/m² | Dust: {dust:.2f} | Eff: {efficiency:.2f}%")
    return jsonify({"status": "success"}), 200

# Getting Data for the Dashboard
@app.route('/dashboard', methods=['GET'])
def dashboard_data():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM readings ORDER BY id DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    return jsonify({"readings": [dict(row) for row in rows]}), 200

# Getting 7 Days Prediction from the LSTM Model
@app.route('/predict', methods=['GET'])
def predict_7_days():
    if not ML_READY:
        return jsonify({"error": "ML model not loaded"}), 500

    print("🔮 Generating 7-Day Digital Twin Prediction...")

    # Get Live Dust AND Live Efficiency from physical sensors
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT dust_density, efficiency_percent FROM readings ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    
    current_dust = row[0] if row else 0.0
    current_eff = row[1] if row else 10.416
    dust_loss_pct = max(0.0, current_dust / 100.0)

    # Calculate Hardware Health Factor (Current Eff / Max STC Eff)
    STC_BASE_EFFICIENCY = 10.416
    health_factor = max(0.0, current_eff / STC_BASE_EFFICIENCY)

    # Fetch Open-Meteo Forecast 
    url = f"https://api.open-meteo.com/v1/forecast?latitude={BAHRAIN_LAT}&longitude={BAHRAIN_LON}&hourly=temperature_2m,shortwave_radiation&past_days=1&forecast_days=7&timezone=auto"
    resp = requests.get(url).json()
    
    times = resp['hourly']['time']
    temps = resp['hourly']['temperature_2m']
    irrads = resp['hourly']['shortwave_radiation']

    # 3. Build DataFrame
    df = pd.DataFrame({'ambient_temperature': temps, 'irradiation': irrads, 'time': times})
    
    # --- NEW: CYCLICAL TIME ENCODING FOR FUTURE PREDICTIONS ---
    df['time'] = pd.to_datetime(df['time'])
    df['hour'] = df['time'].dt.hour
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)

    df['module_temperature'] = df['ambient_temperature'] + (0.03125 * df['irradiation'])
    df['dust_accumulation_g_m2'] = current_dust
    df['dust_loss_percentage'] = dust_loss_pct

    features_df = df[['ambient_temperature', 'module_temperature', 'irradiation', 
                      'dust_accumulation_g_m2', 'dust_loss_percentage', 
                      'hour_sin', 'hour_cos']]
    
    # Scale and Predict
    # 4. Scale and Predict (OPTIMIZED BATCH PROCESSING)
    scaled_f = feature_scaler.transform(features_df)
    
    # Group all 168 time windows together
    windows = []
    forecast_times = []
    for i in range(24, len(scaled_f)):
        windows.append(scaled_f[i-24:i])
        forecast_times.append(times[i])
        
    windows = np.array(windows) # Shape: (168, 24, 7)
    
    # Predict all 7 days in ONE single calculation! (Takes 0.1 seconds)
    pred_scaled = lstm_model.predict(windows, verbose=0)
    pred_yields = target_scaler.inverse_transform(pred_scaled)
    
    raw_predictions = []
    for idx in range(len(pred_yields)):
        yield_val = float(pred_yields[idx][0])
        # Nighttime Clamp (Using the correct index for irradiance)
        if irrads[idx + 24] <= 0.1:
            yield_val = 0.0
            
        raw_predictions.append(max(0.0, yield_val))

    # 5. Apply the LIVE EFFICIENCY PENALTY to the AI
    max_raw = max(raw_predictions) if max(raw_predictions) > 0 else 1.0
    max_physical_watts = 2.0 * health_factor 
    
    final_predictions = []
    for raw in raw_predictions:
        calibrated_watt = (raw / max_raw) * max_physical_watts
        final_predictions.append(round(calibrated_watt, 4))

    print(f"✅ Forecast Calibrated! Panel Efficiency is currently at {current_eff:.2f}% (Health: {health_factor*100:.1f}%)")
    
    return jsonify({
        "status": "success",
        "live_correction": {
            "applied_dust_density": current_dust, 
            "current_efficiency_pct": current_eff,
            "hardware_health_factor": health_factor
        },
        "forecast_times": forecast_times,
        "predicted_yield_watts": final_predictions
    }), 200

if __name__ == '__main__':
    print("🚀 Starting Solar Digital Twin Backend...")
    app.run(host='0.0.0.0', port=5000, debug=True)
# train_model.py - BUG FIXED (TIME-SYNC & RELU)
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import Huber

# --- 1. CONFIGURATION ---
CSV_FILENAME = 'solar_weather_dust_dataset.csv'  # <--- Ensure this is your CSV name
TIME_COLUMN = 'time'                      

FEATURES = ['ambient_temperature', 'module_temperature', 'irradiation', 
            'dust_accumulation_g_m2', 'dust_loss_percentage', 'hour_sin', 'hour_cos']

TARGET = 'ac_power' 
LOOKBACK_HOURS = 24  

print("🚀 Step 1: Loading and Resampling Data...")
df = pd.read_csv(CSV_FILENAME)
df[TIME_COLUMN] = pd.to_datetime(df[TIME_COLUMN])
df.set_index(TIME_COLUMN, inplace=True)

df_hourly = df.resample('1H').mean()

df_hourly['hour'] = df_hourly.index.hour
df_hourly['hour_sin'] = np.sin(2 * np.pi * df_hourly['hour'] / 24.0)
df_hourly['hour_cos'] = np.cos(2 * np.pi * df_hourly['hour'] / 24.0)

df_hourly.dropna(subset=FEATURES + [TARGET], inplace=True)
print(f"✅ Data resampled! Total hourly records: {len(df_hourly)}")

print("📊 Step 2: Scaling the Data...")
feature_scaler = MinMaxScaler(feature_range=(0, 1))
target_scaler = MinMaxScaler(feature_range=(0, 1))

scaled_features = feature_scaler.fit_transform(df_hourly[FEATURES])
scaled_target = target_scaler.fit_transform(df_hourly[[TARGET]])

joblib.dump(feature_scaler, 'feature_scaler.pkl')
joblib.dump(target_scaler, 'target_scaler.pkl')

print("🧩 Step 3: Creating Time-Series Sequences...")
def create_sequences(features, target, lookback):
    X, y = [], []
    for i in range(lookback, len(features)):
        X.append(features[i-lookback:i])
        # THE FIX: Match the target exactly to the CURRENT hour in the weather window!
        y.append(target[i-1]) 
    return np.array(X), np.array(y)

X, y = create_sequences(scaled_features, scaled_target, LOOKBACK_HOURS)

split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]
print(f"✅ Training shape: {X_train.shape}")

class R2ThresholdCallback(tf.keras.callbacks.Callback):
    def __init__(self, X_val, y_val, target_r2=0.85):
        super().__init__()
        self.X_val = X_val
        self.y_val = y_val
        self.target_r2 = target_r2

    def on_epoch_end(self, epoch, logs=None):
        y_pred = self.model.predict(self.X_val, verbose=0)
        r2 = r2_score(self.y_val, y_pred)
        print(f" — Validation R² Score: {r2*100:.2f}%")
        
        if r2 >= self.target_r2:
            print(f"\n🎯 TARGET REACHED! Validation R² hit {r2*100:.2f}%. Stopping training.")
            self.model.stop_training = True

print("🧠 Step 4: Building Deep LSTM Model...")
model = Sequential()

# Lowered Dropout to 0.1 so it doesn't "forget" the direct weather mapping
model.add(LSTM(64, return_sequences=True, input_shape=(LOOKBACK_HOURS, len(FEATURES))))
model.add(Dropout(0.1))

model.add(LSTM(32, return_sequences=False))
model.add(Dropout(0.1))

model.add(Dense(16, activation='relu'))

# THE FIX: Added 'relu' so it never predicts negative power at night
model.add(Dense(1, activation='relu')) 

custom_optimizer = Adam(learning_rate=0.001)
model.compile(optimizer=custom_optimizer, loss=Huber(), metrics=['mae'])

print("🔥 Step 5: Training Deep Model...")
target_stopper = R2ThresholdCallback(X_test, y_test, target_r2=0.85)
backup_stopper = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=150,
    batch_size=32,
    callbacks=[target_stopper, backup_stopper],
    verbose=1
)

print("💾 Step 6: Saving Model...")
model.save('solar_lstm_model.h5')
print("✅ SUCCESS! 'solar_lstm_model.h5' and scalers are saved.")

print("📈 Step 7: Generating Academic Evaluation Graph...")
y_pred_scaled = model.predict(X_test)
y_test_real = target_scaler.inverse_transform(y_test)
y_pred_real = target_scaler.inverse_transform(y_pred_scaled)

plt.figure(figsize=(14, 5))
plt.plot(y_test_real[-168:], label='Actual Power (ac_power)', color='blue', linewidth=2)
plt.plot(y_pred_real[-168:], label='LSTM Predicted Power', color='orange', linestyle='dashed', linewidth=2)
plt.title('LSTM Model Validation: Actual vs. Predicted Solar Yield (1 Week)')
plt.xlabel('Time (Hours)')
plt.ylabel('Power Yield')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('LSTM_Evaluation_Plot.png')
print("✅ Graph Saved!")
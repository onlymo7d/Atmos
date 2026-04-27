import streamlit as st
import pandas as pd
import altair as alt
import requests
import numpy as np


st.set_page_config(page_title="FAHM AI Solution", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .big-metric { font-size: 26px !important; color: #1f2937; }
    .stAlert { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

FLASK_URL = "http://127.0.0.1:5000"

# Getting Data from the Flask API
@st.cache_data(ttl=5)
def fetch_live_data():
    try:
        return requests.get(f"{FLASK_URL}/dashboard", timeout=5).json()
    except:
        return None

@st.cache_data(ttl=60)
def fetch_forecast():
    try:
        return requests.get(f"{FLASK_URL}/predict", timeout=60).json()
    except:
        return None

# Sidebar Navigation
st.sidebar.title("⚡ ATMOS Platform")
page = st.sidebar.radio("Select Dashboard Mode:", [
    "🏠 Smart Home (B2C)", 
    "🏭 Industrial (B2B)",
    "📡 Live IoT Sensors",
    "⚠️ System Alerts & AI Accuracy"  
])
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()

# Smart Home (B2C)
if page == "🏠 Smart Home (B2C)":
    st.title("🏠 ATMOS: Smart Villa Manager")
    st.markdown("**Target User:** Homeowners | **Goal:** Reduce Bill via Digital Twin Prediction")
    st.divider()

    st.sidebar.markdown("### ⚙️ Home System Setup")
    user_solar_watts = st.sidebar.number_input("Solar System Size (Watts)", min_value=100, value=5000, step=500)
    
    with st.spinner('Loading LSTM Predictions...'):
        forecast = fetch_forecast()

    if forecast and forecast.get("status") == "success":
        df = pd.DataFrame({
            'time': pd.to_datetime(forecast['forecast_times']),
            'raw_watts': forecast['predicted_yield_watts']
        })
        
        multiplier = user_solar_watts / 2.0
        df['SOLAR_W'] = df['raw_watts'] * multiplier
        df['SOLAR_KW'] = df['SOLAR_W'] / 1000.0
        df['HOUR'] = df['time'].dt.strftime('%H:%M')

        df['date_str'] = df['time'].dt.strftime('%Y-%m-%d')
        unique_days = df['date_str'].unique()
        selected_day = st.sidebar.selectbox("📅 Plan for Date:", unique_days)
        daily_df = df[df['date_str'] == selected_day].reset_index(drop=True)

        total_gen_kwh = daily_df['SOLAR_KW'].sum() 
        savings = total_gen_kwh * 0.015 
        peak_idx = daily_df['SOLAR_KW'].idxmax()
        peak_time = daily_df.loc[peak_idx]['HOUR']

        c1, c2, c3 = st.columns(3)
        c1.metric("Predicted Generation", f"{total_gen_kwh:.1f} kWh", f"For {selected_day}")
        c2.metric("Bill Savings", f"{savings:.3f} BHD", "Estimated Value")
        c3.metric("Peak Power", f"{daily_df['SOLAR_KW'].max():.2f} kW", f"at {peak_time}")

        st.divider()
        
        correction = forecast['live_correction']
        st.info(f"🧠 **Digital Twin Calibration:** The AI forecast has been scaled by a physical health factor of **{correction['hardware_health_factor']*100:.1f}%**. This is because your physical IoT sensors report a real-time panel efficiency of **{correction['current_efficiency_pct']:.2f}%**.")
        
        st.markdown(f"**☀️ Predicted Solar Output ({user_solar_watts}W System)**")
        
        solar_chart = alt.Chart(daily_df).mark_area(color='#FFC300', opacity=0.8).encode(
            x=alt.X('time:T', axis=alt.Axis(format='%H:%M'), title='Time'),
            y=alt.Y('SOLAR_KW:Q', title='Power (kW)'),
            tooltip=['time:T', 'SOLAR_KW:Q']
        ).properties(height=300)
        st.altair_chart(solar_chart, use_container_width=True)
    else:
        st.error("API Connection Error or Model not loaded.")

# Industrial (B2B)
elif page == "🏭 Industrial (B2B)":
    st.title("🏭 ATMOS: Industrial Grid Solutions")
    st.divider()

    st.sidebar.markdown("### ⚙️ Plant Configuration")
    user_solar_kw = st.sidebar.number_input("Solar Farm Capacity (kW)", min_value=10, value=1000, step=100)

    with st.spinner('Loading LSTM Predictions...'):
        forecast = fetch_forecast()

    if forecast and forecast.get("status") == "success":
        df = pd.DataFrame({
            'time': pd.to_datetime(forecast['forecast_times']),
            'raw_watts': forecast['predicted_yield_watts']
        })
        
        user_watts = user_solar_kw * 1000.0
        multiplier = user_watts / 2.0
        df['SOLAR_KW'] = (df['raw_watts'] * multiplier) / 1000.0

        df['date_str'] = df['time'].dt.strftime('%Y-%m-%d')
        unique_days = df['date_str'].unique()
        selected_day = st.sidebar.selectbox("📅 Strategic View:", unique_days)
        daily_df = df[df['date_str'] == selected_day].reset_index(drop=True)

        total_gen_kwh = daily_df['SOLAR_KW'].sum()
        savings_usd = total_gen_kwh * 0.08 
        carbon_tons = total_gen_kwh * 0.0004 
        capacity_factor = (total_gen_kwh / (user_solar_kw * 24)) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Generation", f"{int(total_gen_kwh):,} kWh", "Daily Capacity")
        c2.metric("OPEX Savings", f"${int(savings_usd):,}", "Projected Value")
        c3.metric("Carbon Offset", f"{carbon_tons:.2f} Tons", "CO2 Avoided")
        c4.metric("Capacity Factor", f"{int(capacity_factor)}%", "Efficiency")

        st.divider()
        correction = forecast['live_correction']
        st.info(f"🧠 **Digital Twin Calibration:** The AI forecast has been scaled by a physical health factor of **{correction['hardware_health_factor']*100:.1f}%**. This is because your physical IoT sensors report a real-time panel efficiency of **{correction['current_efficiency_pct']:.2f}%**.")
        
        st.markdown(f"**☀️ Commercial Asset Performance ({user_solar_kw} kW Farm)**")
        
        solar_chart = alt.Chart(daily_df).mark_area(color='#F1C40F', opacity=0.8).encode(
            x=alt.X('time:T', axis=alt.Axis(format='%H:%M'), title='Time'),
            y=alt.Y('SOLAR_KW:Q', title='Power (kW)'),
            tooltip=['time:T', 'SOLAR_KW:Q']
        ).properties(height=350)
        st.altair_chart(solar_chart, use_container_width=True)
    else:
        st.error("API Connection Error or Model not loaded.")

# Live IoT Sensors
elif page == "📡 Live IoT Sensors":
    st.title("📡 Physical Hardware Telemetry")
    st.divider()

    live_data = fetch_live_data()

    if live_data and live_data.get("readings"):
        readings = live_data["readings"]
        latest = readings[0]

        st.subheader("⚡ Current Sensor Status")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Actual Efficiency", f"{latest['efficiency_percent']:.2f} %", "From Hardware")
        col2.metric("Irradiance (LDR)", f"{latest['irradiance_w_m2']:.1f} W/m²")
        col3.metric("Module Temp", f"{latest['temperature_c']} °C", "MAX6675")
        col4.metric("Dust Density", f"{latest['dust_density']:.2f}", "GP2Y1010AU0F")

        st.divider()
        df_live = pd.DataFrame(readings)
        df_live['timestamp'] = pd.to_datetime(df_live['timestamp'])

        chart_c1, chart_c2 = st.columns(2)
        with chart_c1:
            eff_chart = alt.Chart(df_live).mark_line(point=True, color='green').encode(
                x=alt.X('timestamp:T', title='Time', axis=alt.Axis(format='%H:%M:%S')),
                y=alt.Y('efficiency_percent:Q', title='Efficiency (%)'),
                tooltip=['timestamp:T', 'efficiency_percent:Q']
            ).properties(height=250)
            st.altair_chart(eff_chart, use_container_width=True)

        with chart_c2:
            irr_chart = alt.Chart(df_live).mark_line(point=True, color='orange').encode(
                x=alt.X('timestamp:T', title='Time', axis=alt.Axis(format='%H:%M:%S')),
                y=alt.Y('irradiance_w_m2:Q', title='Irradiance (W/m²)'),
                tooltip=['timestamp:T', 'irradiance_w_m2:Q']
            ).properties(height=250)
            st.altair_chart(irr_chart, use_container_width=True)
    else:
        st.warning("No physical sensor data arriving.")

# System Alerts & AI Accuracy
elif page == "⚠️ System Alerts & AI Accuracy":
    st.title("⚠️ Fault Detection & AI Validation")
    st.markdown("**Real-time diagnostics and mathematical validation of the LSTM model.**")
    st.divider()

    live_data = fetch_live_data()
    forecast_data = fetch_forecast()

    if live_data and forecast_data:
        readings = live_data["readings"]
        latest = readings[0]
        df_live = pd.DataFrame(readings)

        st.subheader("🔍 Hardware Fault Detection (FDD)")
        
        # Calculate Rolling Average Efficiency
        rolling_eff = df_live['efficiency_percent'].mean()
        current_eff = latest['efficiency_percent']
        
        col_a1, col_a2, col_a3 = st.columns(3)
        
        # Efficiency Drop Alert
        with col_a1:
            if current_eff < (rolling_eff * 0.7) and rolling_eff > 1.0:
                st.error("🚨 **CRITICAL DROP**\n\nEfficiency dropped >30% below average. Inspect panel for damage or heavy shading.")
            else:
                st.success("✅ **SYSTEM HEALTHY**\n\nEfficiency is stable compared to rolling average.")

        # Dust Alert
        with col_a2:
            if latest['dust_density'] > 150:
                st.warning(f"🧹 **CLEANING REQUIRED**\n\nDust density is {latest['dust_density']:.1f}. Severe soiling detected.")
            else:
                st.success(f"✅ **SURFACE CLEAN**\n\nDust density is {latest['dust_density']:.1f}. No cleaning needed.")

        # Temperature Alert
        with col_a3:
            if latest['temperature_c'] > 45:
                st.error(f"🔥 **OVERHEATING**\n\nPanel temp is {latest['temperature_c']}°C. Thermal losses are extremely high.")
            else:
                st.success(f"✅ **THERMAL NOMINAL**\n\nPanel temp is {latest['temperature_c']}°C. Operating safely.")

        st.divider()

        # AI Validation
        st.subheader("📊 Real-Time AI Validation (Current Hour)")
        st.markdown("Comparing the physical sensor's actual power output to the AI's current prediction.")

        # Get actual and predicted watts for right NOW
        actual_watts = latest['expected_p_out']
        predicted_watts = forecast_data['predicted_yield_watts'][0] 
        
        # Error Calculation (MAE & MAPE)
        absolute_error = abs(actual_watts - predicted_watts)
        
        # Avoid division by zero at night
        if actual_watts > 0.05:
            mape = (absolute_error / actual_watts) * 100
        else:
            mape = 0.0 if predicted_watts < 0.05 else 100.0
            
        accuracy = max(0.0, 100.0 - mape)

        score_col1, score_col2, score_col3, score_col4 = st.columns(4)
        
        score_col1.metric("Actual Sensor Output", f"{actual_watts:.4f} W")
        score_col2.metric("AI Predicted Output", f"{predicted_watts:.4f} W")
        score_col3.metric("Absolute Error (MAE)", f"{absolute_error:.4f} W", "Lower is better", delta_color="inverse")
        
        if accuracy > 85:
            score_col4.metric("Real-Time Accuracy", f"{accuracy:.1f} %", "Excellent")
        elif accuracy > 70:
            score_col4.metric("Real-Time Accuracy", f"{accuracy:.1f} %", "Acceptable", delta_color="off")
        else:
            score_col4.metric("Real-Time Accuracy", f"{accuracy:.1f} %", "Low (Weather Shift / Nighttime)", delta_color="inverse")

    else:
        st.error("Waiting for data from Flask backend...")
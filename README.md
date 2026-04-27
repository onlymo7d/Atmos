
<div align="center">

# ☀️ ATMOS
### Solar-IoT Digital Twin & Deep Learning Forecaster

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=flat&logo=tensorflow&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino-00979D?style=flat&logo=arduino&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-C51A4A?style=flat&logo=raspberry-pi&logoColor=white)

> A physical-to-virtual Digital Twin system that monitors real-time solar panel degradation using custom IoT hardware, fused with a Deep Learning LSTM model to predict future energy generation, detect faults, and calculate financial savings.

🏆 **Awarded highest possible grade at NCST Graduation Defense**

</div>

---

## 🌟 Key Features

| Feature | Description |
|---------|-------------|
| 🔬 Physical Digital Twin | Scales a 2W hardware prototype to MW-level industrial simulation (B2B & B2C) |
| 🧠 LSTM Forecasting | Multi-layer DNN with Huber Loss, Cyclical Time Encoding & nighttime clamping |
| ⚠️ Fault Detection (FDD) | Real-time anomaly detection for dust soiling & thermal overloading with live MAPE |
| 📊 Dynamic Dashboard | Streamlit UI with B2B/B2C views, Open-Meteo weather API & ESG Carbon tracking |

---

## 🏗️ System Architecture

```
Physical Layer      Engine Layer       AI Layer           Interface Layer
──────────────      ────────────       ────────           ───────────────
Arduino Nano   →    Flask REST API →   LSTM Model    →    Streamlit Dashboard
GP2Y Dust Sensor    SQLite DB          7-input / 7-day    B2B & B2C Views
LDR + MAX6675       Open-Meteo API     sliding window     CSV Export
Raspberry Pi        bridge.py          train_model.py     dashboard.py
```

---

## ⚙️ Installation & Setup

### 1. Install Dependencies
```bash
pip install flask flask-cors pandas numpy requests plotly altair streamlit scikit-learn tensorflow h5py
```

### 2. Hardware Setup (Raspberry Pi)
Update the Flask URL in `bridge.py`:
```python
FLASK_URL = 'http://<YOUR_LAPTOP_IP>:5000/sensor'
```
Then run:
```bash
python bridge.py
```

### 3. Backend (Laptop/PC)
```bash
python app.py
```

### 4. Dashboard (New Terminal)
```bash
streamlit run dashboard.py
```

---

## 📂 Project Structure

```
ATMOS/
├── app.py                   # Flask REST API & Database Manager
├── dashboard.py             # Streamlit B2B/B2C Dashboard
├── bridge.py                # Raspberry Pi Serial-to-WiFi Bridge
├── train_model.py           # LSTM Training Script
├── solar_lstm_model.h5      # Trained TensorFlow Model
├── feature_scaler.pkl       # MinMax Input Scaler
├── target_scaler.pkl        # MinMax Output Scaler
├── solar_data.db            # SQLite Database (auto-generated)
└── README.md
```

---

## 🧠 ML Model Details

- **Architecture:** Multi-layer LSTM (Long Short-Term Memory)
- **Target:** `ac_power` — instantaneous yield (avoids cumulative sum errors)
- **Inputs (7):** Ambient Temp · Module Temp · Irradiance · Dust Accumulation · Dust Loss % · Hour Sin · Hour Cos
- **Window:** 24-hour sliding window → 7-day future forecast
- **Loss Function:** Huber Loss (robust to outliers)
- **Constraint:** Nighttime clamping — Yield = 0 when Irradiance ≤ 0.1
- **Training:** R² threshold callback to prevent overfitting

---

## 🙏 Acknowledgments

- **NCST** — for the educational foundation and resources
- **Ayesha Abdulljalil, Mohammed Salman & Khalid Maroof** — for guidance and dedication
- **Dr. Mohammed Mazen (University of Bahrain)** — for expert mentorship that elevated the technical architecture

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/onlymo7d">Mohammed</a></sub>
</div>

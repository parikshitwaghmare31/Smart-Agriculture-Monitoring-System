# 🌱 Smart Agriculture Monitoring System

![CI](https://github.com/YOUR_USERNAME/smart-agriculture-monitoring/actions/workflows/ci.yml/badge.svg)

An end-to-end **IoT + AI** system that collects real-time soil moisture,
temperature, and humidity data from field sensors (real ESP32 hardware or a
Python simulator), stores it in MongoDB, and uses a trained machine learning
model to recommend **whether and how much to irrigate**. A React dashboard
visualizes live readings, historical trends, and predictions.

Built with production practices in mind: clean layered architecture,
environment-based configuration, structured logging, health checks, and a
full Docker Compose stack.

---

## ✨ Features

- 📡 **Real-time sensor ingestion** via MQTT (Mosquitto broker) or REST
- 🔌 **ESP32 firmware included** (`mqtt-simulator/esp32_sketch.ino`) — swap
  in real hardware with zero backend changes
- 🐍 **Python IoT simulator** for development without physical hardware
- 🧠 **ML-powered irrigation prediction**: RandomForest classifier (irrigate
  YES/NO) + RandomForest regressor (liters of water to apply)
- 🗄️ **MongoDB** for sensor history and prediction logs
- 📊 **React dashboard**: live sensor cards, trend charts (Recharts),
  interactive prediction panel
- 🐳 **Full Docker Compose stack**: backend, frontend, MongoDB, Mosquitto,
  and the IoT simulator all start with one command
- 🧾 Structured logging (loguru), input validation (Pydantic), and a
  `/health` endpoint for monitoring

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python, FastAPI, Motor (async MongoDB driver) |
| Database | MongoDB |
| Messaging | MQTT (Eclipse Mosquitto) |
| ML | scikit-learn (RandomForest), joblib |
| Frontend | React, Recharts, Axios |
| IoT | ESP32 (real) or Python `paho-mqtt` simulator |
| DevOps | Docker, Docker Compose, nginx |

---

## 📁 Project Structure

```
smart-agriculture/
├── backend/
│   ├── app/
│   │   ├── config/       # settings, logging, MongoDB connection
│   │   ├── models/       # Pydantic schemas
│   │   ├── routes/       # sensor-data, predict, history, health
│   │   ├── services/     # ML inference service, MQTT client service
│   │   └── main.py       # FastAPI app + lifespan wiring
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/   # SensorCard, SensorChart, PredictionPanel
│   │   ├── pages/        # Dashboard
│   │   └── services/     # api.js (Axios client)
│   └── package.json
├── ml/
│   ├── scripts/
│   │   ├── generate_dataset.py   # synthetic agronomic dataset generator
│   │   └── train_model.py        # trains + saves classifier + regressor
│   ├── data/              # irrigation_dataset.csv
│   └── models/            # irrigation_model.pkl, metrics.json
├── mqtt-simulator/
│   ├── simulator.py       # Python ESP32 simulator
│   ├── esp32_sketch.ino   # real ESP32 firmware
│   └── requirements.txt
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.simulator
│   ├── nginx.conf
│   └── mosquitto.conf
├── docs/
│   ├── LOCAL_SETUP.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── GITHUB_GUIDE.md
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🔌 REST API

Base path: `/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/sensor-data` | Manually submit a sensor reading |
| `GET` | `/sensor-data/latest?limit=10` | Most recent readings |
| `POST` | `/predict` | Get an irrigation recommendation for given readings |
| `GET` | `/history/sensors?device_id=&limit=` | Historical sensor data (for charts) |
| `GET` | `/history/predictions?device_id=&limit=` | Historical predictions |
| `GET` | `/health` | Service health (Mongo, MQTT, model status) |

Interactive Swagger docs available at `/docs` once the backend is running.

**Example: request a prediction**
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"soil_moisture": 22, "temperature": 34, "humidity": 28}'
```
```json
{
  "irrigate": true,
  "confidence": 0.97,
  "water_amount_liters": 28.4,
  "reasoning": "Soil moisture 22% is low relative to temperature 34°C and humidity 28%, indicating irrigation is needed.",
  "timestamp": "2026-07-15T09:00:00Z"
}
```

---

## 🧠 Machine Learning

- **Input features**: `soil_moisture (%)`, `temperature (°C)`, `humidity (%)`
- **Outputs**:
  - Classification: `irrigate` (YES/NO) via `RandomForestClassifier`
  - Regression: `water_amount_l` (liters) via `RandomForestRegressor`,
    trained only on irrigate=YES samples
- **Training data**: synthetic but agronomically-grounded (`generate_dataset.py`
  encodes real irrigation heuristics — dry soil + heat + low humidity raises
  irrigation need — plus Gaussian noise for realism). Swap in real historical
  sensor + irrigation-outcome data once you've collected enough from the field.
- **Current test-set metrics** (see `ml/models/metrics.json`): ~86% accuracy,
  ~92% precision on the classifier; MAE ≈ 2.2 L on the regressor.
- If no trained model file is present, the API automatically falls back to a
  transparent rule-based heuristic so it never hard-fails.

Retrain anytime:
```bash
cd ml/scripts
python generate_dataset.py
python train_model.py
```

---

## 🚀 Quick Start (Docker — recommended)

```bash
git clone <your-repo-url>
cd smart-agriculture

# Train the model once so it's available to bake into the backend image
cd ml/scripts && pip install -r ../../backend/requirements.txt
python generate_dataset.py && python train_model.py
cd ../..

docker compose up -d --build
```

Then open:
- Frontend dashboard: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- MongoDB: `localhost:27017`
- MQTT broker: `localhost:1883`

The `iot-simulator` container starts automatically and begins publishing
fake sensor data for 3 virtual devices every 5 seconds — the dashboard should
populate within seconds.

For a non-Docker local setup, see **`docs/LOCAL_SETUP.md`**.
For cloud deployment (Render, Railway, AWS EC2), see **`docs/DEPLOYMENT_GUIDE.md`**.
For Git/GitHub workflow, see **`docs/GITHUB_GUIDE.md`**.

---

## 📸 Screenshots

> _Add screenshots after running the app locally:_
- `docs/screenshots/dashboard-overview.png` — live sensor cards + trend chart
- `docs/screenshots/prediction-panel.png` — irrigation prediction result
- `docs/screenshots/swagger-docs.png` — API documentation

---

## ✅ Testing & CI

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs automatically on
every push and pull request to `main`:

| Job | What it checks |
|---|---|
| `ml-pipeline` | Regenerates the dataset, retrains the model, and enforces a quality gate (fails the build if classifier accuracy or F1 drops below 0.75) |
| `backend-test` | Confirms the FastAPI app imports cleanly and runs `pytest` smoke tests (route registration, ML service predictions) — no MongoDB/MQTT required |
| `frontend-build` | Installs locked dependencies (`npm ci`) and produces a production build |
| `docker-build` | Builds all three Dockerfiles (backend, frontend, simulator) to catch broken images before merge |

Run the backend tests locally:
```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

> Remember to replace `YOUR_USERNAME` in the CI badge URL above with your
> actual GitHub username/org once you push this repo.

---

## 🗺️ Possible Extensions

- Push notifications / email alerts when soil moisture crosses a threshold
- Multi-farm / multi-field support with per-field dashboards
- Weather API integration to factor in forecasted rain
- Replace synthetic training data with real historical data once collected
- Role-based auth (farm owner vs. field technician)

---

## 📄 License

MIT — free to use for learning, portfolios, and derivative projects.

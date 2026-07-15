# Local Development Guide — Smart Agriculture Monitoring System

This guide covers running every piece of the system **without Docker**, useful
for active development and debugging. For a one-command setup, see the Docker
section in the main README instead.

## 0. Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- MongoDB running locally (or a free MongoDB Atlas cluster)
- Mosquitto MQTT broker (or any MQTT broker)

Install Mosquitto:
```bash
# macOS
brew install mosquitto

# Ubuntu/Debian
sudo apt-get install mosquitto mosquitto-clients
```

## 1. Start MongoDB

```bash
# If installed locally
mongod --dbpath ./mongo-data

# OR run it in Docker just for this piece
docker run -d --name mongo -p 27017:27017 mongo:7
```

## 2. Start the MQTT broker

```bash
mosquitto -v
# OR
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto:2
```

## 3. Train the ML model (first time only)

```bash
cd ml/scripts
pip install -r ../../backend/requirements.txt
python generate_dataset.py     # creates ml/data/irrigation_dataset.csv
python train_model.py          # creates ml/models/irrigation_model.pkl
```

You should see accuracy/precision/recall metrics printed and a
`ml/models/irrigation_model.pkl` file created.

## 4. Run the backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: for local (non-Docker) runs, set:
#   MONGO_URI=mongodb://localhost:27017
#   MQTT_BROKER_HOST=localhost
#   MODEL_PATH=<absolute path>/ml/models/irrigation_model.pkl

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's running:
```bash
curl http://localhost:8000/api/v1/health
```

Interactive API docs (Swagger UI): http://localhost:8000/docs

## 5. Run the IoT simulator

In a new terminal:
```bash
cd mqtt-simulator
pip install -r requirements.txt
python simulator.py --devices 3 --interval 5 --broker localhost
```

You should see the backend logs acknowledging incoming sensor readings, and
`GET /api/v1/sensor-data/latest` should start returning data.

## 6. Run the frontend (React)

```bash
cd frontend
npm install
```

Add this to `frontend/package.json` for local dev proxying (if not already present):
```json
"proxy": "http://localhost:8000"
```

```bash
npm start
```

Open http://localhost:3000 — you should see live sensor cards, a trend chart,
and the irrigation prediction panel.

## 7. Quick manual test with curl

```bash
# Push a manual sensor reading
curl -X POST http://localhost:8000/api/v1/sensor-data \
  -H "Content-Type: application/json" \
  -d '{"device_id":"manual-01","soil_moisture":22,"temperature":34,"humidity":28}'

# Request a prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"soil_moisture":22,"temperature":34,"humidity":28}'

# View history
curl http://localhost:8000/api/v1/history/sensors?limit=20
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `mongo_connected: false` in `/health` | Confirm MongoDB is running and `MONGO_URI` in `.env` is correct |
| `mqtt_connected: false` | Confirm Mosquitto is running on the configured host/port |
| Predictions use "rule-based fallback" | Model file missing — re-run `train_model.py` and check `MODEL_PATH` |
| CORS errors in browser console | Set `CORS_ORIGINS` in backend `.env` to include your frontend origin |

# Deployment Guide — Smart Agriculture Monitoring System

This project ships as four containers (backend, frontend, MongoDB, Mosquitto)
plus an optional simulator container. Below are three deployment paths,
from easiest to most control.

---

## Option A: Render (easiest, good for demos/portfolios)

Render can deploy directly from your Dockerfiles.

1. Push this repo to GitHub (see `docs/GITHUB_GUIDE.md`).
2. On Render, create a **Web Service** for the backend:
   - Repository: your repo
   - Root directory: repo root
   - Dockerfile path: `docker/Dockerfile.backend`
   - Environment variables (Render dashboard → Environment):
     ```
     MONGO_URI=<your MongoDB Atlas connection string>
     MONGO_DB_NAME=smart_agriculture
     MQTT_BROKER_HOST=<your hosted broker, e.g. HiveMQ Cloud>
     MQTT_BROKER_PORT=8883
     MQTT_ENABLED=true
     MODEL_PATH=/app/ml/models/irrigation_model.pkl
     CORS_ORIGINS=https://<your-frontend-domain>
     ```
   - Instance type: Free or Starter is enough for a demo.
3. Create a **Static Site** for the frontend:
   - Root directory: `frontend`
   - Build command: `npm install && npm run build`
   - Publish directory: `build`
   - Environment variable: `REACT_APP_API_BASE_URL=https://<your-backend>.onrender.com/api/v1`
4. For MongoDB, use **MongoDB Atlas** free tier instead of self-hosting — Render's
   free plan doesn't support persistent disks well for stateful services.
5. For MQTT, use a managed broker like **HiveMQ Cloud** (free tier) or **CloudAMQP**
   instead of self-hosting Mosquitto, since Render's free web services sleep and
   aren't ideal for always-on broker processes.

---

## Option B: Railway

1. `railway login` and `railway init` in the repo root.
2. Add services from the dashboard, pointing each at its Dockerfile:
   - `docker/Dockerfile.backend`
   - `docker/Dockerfile.frontend`
3. Add a MongoDB plugin from Railway's template marketplace (or use Atlas).
4. Add environment variables the same way as Render, above.
5. Railway auto-assigns public domains — use the backend's domain in the
   frontend's `REACT_APP_API_BASE_URL` build variable.
6. For MQTT, Railway can host Mosquitto as a service too (deploy from the
   `eclipse-mosquitto` image with a custom start command using
   `docker/mosquitto.conf`), or use a managed broker as in Option A.

---

## Option C: AWS EC2 (full control, closest to "real" production)

This runs the exact same `docker-compose.yml` as local dev.

1. **Launch an EC2 instance** (Ubuntu 22.04, t3.medium or larger recommended
   since you're running 4-5 containers including MongoDB).
2. **Open ports** in the security group: 22 (SSH), 80/443 (frontend), 8000
   (backend API), 1883 (MQTT — restrict to trusted IPs or your VPN).
3. **Install Docker + Docker Compose**:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-plugin
   sudo usermod -aG docker $USER
   ```
4. **Clone your repo**:
   ```bash
   git clone https://github.com/<you>/smart-agriculture.git
   cd smart-agriculture
   ```
5. **Set production environment variables** — create `docker-compose.override.yml`
   or edit the `environment:` blocks in `docker-compose.yml` with real secrets
   (never commit real secrets to Git).
6. **Build and run**:
   ```bash
   docker compose up -d --build
   ```
7. **Put nginx/Certbot or an AWS Application Load Balancer in front** for
   HTTPS termination. A simple approach: point a domain at the EC2 instance
   and use Certbot to get a free TLS cert for the frontend's nginx.
8. **Persistent data**: the `mongo_data` named volume in `docker-compose.yml`
   already persists MongoDB data across container restarts. For true
   production durability, snapshot the EBS volume regularly or migrate to
   MongoDB Atlas.
9. **Auto-restart on reboot**: containers are set to `restart: unless-stopped`,
   and you should also enable the Docker service itself:
   ```bash
   sudo systemctl enable docker
   ```

---

## Environment Variables Reference

| Variable | Description | Example |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net` |
| `MONGO_DB_NAME` | Database name | `smart_agriculture` |
| `MQTT_BROKER_HOST` | MQTT broker hostname | `broker.hivemq.cloud` |
| `MQTT_BROKER_PORT` | MQTT broker port | `8883` (TLS) or `1883` |
| `MQTT_TOPIC` | Topic sensors publish to | `farm/sensors` |
| `MQTT_ENABLED` | Toggle MQTT client | `true` / `false` |
| `MODEL_PATH` | Path to trained `.pkl` inside the container | `/app/ml/models/irrigation_model.pkl` |
| `CORS_ORIGINS` | Allowed frontend origins | `https://myapp.com` |
| `REACT_APP_API_BASE_URL` | Frontend build-time API URL | `https://api.myapp.com/api/v1` |

## Production Tips

- **Never** commit real `.env` files or credentials — only `.env.example` should be in Git.
- Use MongoDB Atlas or another managed database in production rather than a
  container with a Docker volume — much better durability and backups.
- Put the MQTT broker behind TLS (port 8883) in production; port 1883 is
  unencrypted and fine only for local development.
- Rotate the trained model periodically: re-run `ml/scripts/train_model.py`
  against real historical sensor data (once you have enough of it) instead of
  the synthetic dataset, then rebuild the backend image.
- Add a reverse proxy (nginx, Traefik, or a cloud load balancer) in front of
  the backend for TLS termination and rate limiting.
- Monitor `/api/v1/health` with an uptime checker (e.g. UptimeRobot, AWS
  CloudWatch) to catch MongoDB/MQTT disconnects early.

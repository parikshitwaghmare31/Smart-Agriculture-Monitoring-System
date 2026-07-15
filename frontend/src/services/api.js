import axios from "axios";

// In Docker this is proxied/rewritten by nginx; in local dev CRA proxy handles it (see package.json "proxy")
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

export const getLatestReadings = (limit = 10) =>
  api.get(`/sensor-data/latest`, { params: { limit } }).then((r) => r.data);

export const getSensorHistory = (deviceId, limit = 100) =>
  api
    .get(`/history/sensors`, { params: { device_id: deviceId, limit } })
    .then((r) => r.data);

export const getPredictionHistory = (deviceId, limit = 50) =>
  api
    .get(`/history/predictions`, { params: { device_id: deviceId, limit } })
    .then((r) => r.data);

export const requestPrediction = (payload) =>
  api.post(`/predict`, payload).then((r) => r.data);

export const submitSensorReading = (payload) =>
  api.post(`/sensor-data`, payload).then((r) => r.data);

export const checkHealth = () => api.get(`/health`).then((r) => r.data);

export default api;

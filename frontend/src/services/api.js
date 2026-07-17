import axios from "axios";

// In Docker this is proxied/rewritten by nginx; in local dev CRA proxy handles it (see package.json "proxy")
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

// Attach the JWT bearer token (if present) to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the token is invalid/expired, clear it and force back to the login
// screen rather than showing a confusing broken dashboard.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export const getLatestReadings = (limit = 10, deviceId = null) =>
  api
    .get(`/sensor-data/latest`, { params: { limit, device_id: deviceId } })
    .then((r) => r.data);

export const getDevices = () =>
  api.get(`/sensor-data/devices`).then((r) => r.data);

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

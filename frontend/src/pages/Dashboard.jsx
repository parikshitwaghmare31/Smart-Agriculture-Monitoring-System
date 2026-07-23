import React, { useEffect, useState, useCallback } from "react";
import SensorCard from "../components/SensorCard";
import PredictionPanel from "../components/PredictionPanel";
import SensorChart from "../components/SensorChart";
import DeviceSelector from "../components/DeviceSelector";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { getLatestReadings, getSensorHistory, getDevices, checkHealth } from "../services/api";
import { useLanguage } from "../i18n/LanguageContext";

const POLL_INTERVAL_MS = 5000;

export default function Dashboard({ user, onLogout, onOpenAdminPanel, onOpenDiseaseClassifier, onOpenProfile }) {
  const { t } = useLanguage();
  const [latest, setLatest] = useState(null);
  const [history, setHistory] = useState([]);
  const [devices, setDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState(null); // null = "All devices"
  const [health, setHealth] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const [latestReadings, historyData, devicesData, healthData] = await Promise.all([
        getLatestReadings(1, selectedDeviceId),
        getSensorHistory(selectedDeviceId, 50),
        getDevices(),
        checkHealth(),
      ]);
      if (latestReadings && latestReadings.length > 0) {
        setLatest(latestReadings[0]);
      } else {
        setLatest(null); // e.g. selected device has no readings yet
      }
      setHistory(historyData.data || []);
      setDevices(devicesData.devices || []);
      setHealth(healthData);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to refresh dashboard data", err);
    }
  }, [selectedDeviceId]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  const selectedDevice = selectedDeviceId
    ? devices.find((d) => d.device_id === selectedDeviceId)
    : null;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>🌱 {t("appTitle")}</h1>
          <p className="subtitle">
            {selectedDeviceId
              ? `${t("viewingDevice")}: ${selectedDeviceId}`
              : latest
              ? `${t("viewingAllDevices")} (${latest.device_id})`
              : t("waitingForData")}
          </p>
        </div>
        <div className="dashboard-header-right">
          <LanguageSwitcher />
          <div className={`status-badge ${health?.mongo_connected ? "online" : "offline"}`}>
            {health?.mongo_connected ? `● ${t("live")}` : `● ${t("disconnected")}`}
          </div>
        </div>
      </header>

      <div className="user-bar">
        <span className="user-bar-name">
          👤 {user?.full_name} <span className="muted-text">({user?.role})</span>
        </span>
        <div className="user-bar-actions">
          <button className="btn-secondary" onClick={onOpenProfile}>
            ⚙️ {t("myProfile")}
          </button>
          <button className="btn-secondary" onClick={onOpenDiseaseClassifier}>
            🌿 {t("diseaseClassifier")}
          </button>
          {user?.role === "admin" && (
            <button className="btn-secondary" onClick={onOpenAdminPanel}>
              🛠️ {t("adminPanel")}
            </button>
          )}
          <button className="btn-secondary" onClick={onLogout}>
            {t("signOut")}
          </button>
        </div>
      </div>

      <DeviceSelector
        devices={devices}
        selectedDeviceId={selectedDeviceId}
        onSelect={setSelectedDeviceId}
      />

      {devices.length === 0 && (
        <div className="empty-state-banner">
          {user?.role === "admin" ? t("noDevicesRegisteredAdmin") : t("noDevicesRegisteredFarmer")}
        </div>
      )}

      {devices.length > 0 && selectedDevice && !selectedDevice.has_data && (
        <div className="empty-state-banner">
          "{selectedDevice.label || selectedDevice.device_id}" {t("deviceNoDataYet")}
        </div>
      )}

      <section className="sensor-cards">
        <SensorCard
          title={t("soilMoisture")}
          value={latest?.soil_moisture}
          unit="%"
          icon="💧"
          low={25}
          high={80}
        />
        <SensorCard
          title={t("temperature")}
          value={latest?.temperature}
          unit="°C"
          icon="🌡️"
          low={15}
          high={35}
        />
        <SensorCard
          title={t("humidity")}
          value={latest?.humidity}
          unit="%"
          icon="☁️"
          low={30}
          high={80}
        />
      </section>

      <section className="dashboard-grid">
        <SensorChart data={history} />
        <PredictionPanel latestReading={latest} selectedDeviceId={selectedDeviceId} />
      </section>

      <footer className="dashboard-footer">
        {lastUpdated && `${t("lastUpdated")}: ${lastUpdated.toLocaleTimeString()}`}
      </footer>
    </div>
  );
}

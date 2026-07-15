import React, { useEffect, useState, useCallback } from "react";
import SensorCard from "../components/SensorCard";
import PredictionPanel from "../components/PredictionPanel";
import SensorChart from "../components/SensorChart";
import { getLatestReadings, getSensorHistory, checkHealth } from "../services/api";

const POLL_INTERVAL_MS = 5000;

export default function Dashboard() {
  const [latest, setLatest] = useState(null);
  const [history, setHistory] = useState([]);
  const [health, setHealth] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const [latestReadings, historyData, healthData] = await Promise.all([
        getLatestReadings(1),
        getSensorHistory(null, 50),
        checkHealth(),
      ]);
      if (latestReadings && latestReadings.length > 0) {
        setLatest(latestReadings[0]);
      }
      setHistory(historyData.data || []);
      setHealth(healthData);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to refresh dashboard data", err);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>🌱 Smart Agriculture Monitoring</h1>
          <p className="subtitle">
            {latest ? `Device: ${latest.device_id}` : "Waiting for sensor data..."}
          </p>
        </div>
        <div className={`status-badge ${health?.mongo_connected ? "online" : "offline"}`}>
          {health?.mongo_connected ? "● Live" : "● Disconnected"}
        </div>
      </header>

      <section className="sensor-cards">
        <SensorCard
          title="Soil Moisture"
          value={latest?.soil_moisture}
          unit="%"
          icon="💧"
          low={25}
          high={80}
        />
        <SensorCard
          title="Temperature"
          value={latest?.temperature}
          unit="°C"
          icon="🌡️"
          low={15}
          high={35}
        />
        <SensorCard
          title="Humidity"
          value={latest?.humidity}
          unit="%"
          icon="☁️"
          low={30}
          high={80}
        />
      </section>

      <section className="dashboard-grid">
        <SensorChart data={history} />
        <PredictionPanel latestReading={latest} />
      </section>

      <footer className="dashboard-footer">
        {lastUpdated && `Last updated: ${lastUpdated.toLocaleTimeString()}`}
      </footer>
    </div>
  );
}

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export default function SensorChart({ data }) {
  const formatted = data.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString(),
    soil_moisture: d.soil_moisture,
    temperature: d.temperature,
    humidity: d.humidity,
  }));

  return (
    <div className="panel">
      <h3>Sensor Trends</h3>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis dataKey="time" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="soil_moisture" stroke="#2e7d32" name="Soil Moisture (%)" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="temperature" stroke="#e65100" name="Temperature (°C)" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="humidity" stroke="#0277bd" name="Humidity (%)" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

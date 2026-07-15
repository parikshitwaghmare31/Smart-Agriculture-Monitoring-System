import React from "react";

function statusColor(value, low, high) {
  if (value < low) return "#e53935"; // red - critical low
  if (value > high) return "#fb8c00"; // orange - high
  return "#43a047"; // green - normal
}

export default function SensorCard({ title, value, unit, icon, low, high }) {
  const color = statusColor(value, low, high);
  return (
    <div className="sensor-card" style={{ borderTop: `4px solid ${color}` }}>
      <div className="sensor-card-icon">{icon}</div>
      <div className="sensor-card-title">{title}</div>
      <div className="sensor-card-value" style={{ color }}>
        {value !== null && value !== undefined ? value.toFixed(1) : "--"}
        <span className="sensor-card-unit">{unit}</span>
      </div>
    </div>
  );
}

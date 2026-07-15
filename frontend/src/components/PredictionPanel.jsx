import React, { useState } from "react";
import { requestPrediction } from "../services/api";

export default function PredictionPanel({ latestReading }) {
  const [form, setForm] = useState({ soil_moisture: 40, temperature: 28, humidity: 50 });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const useLiveReading = () => {
    if (!latestReading) return;
    setForm({
      soil_moisture: latestReading.soil_moisture,
      temperature: latestReading.temperature,
      humidity: latestReading.humidity,
    });
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: parseFloat(e.target.value) });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await requestPrediction({ ...form, device_id: "dashboard-manual" });
      setResult(data);
    } catch (err) {
      setError("Prediction request failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>Irrigation Prediction</h3>
        <button className="btn-secondary" onClick={useLiveReading} type="button">
          Use Latest Reading
        </button>
      </div>

      <form onSubmit={handleSubmit} className="prediction-form">
        <label>
          Soil Moisture (%)
          <input type="number" name="soil_moisture" value={form.soil_moisture} onChange={handleChange} min="0" max="100" step="0.1" required />
        </label>
        <label>
          Temperature (°C)
          <input type="number" name="temperature" value={form.temperature} onChange={handleChange} min="-10" max="60" step="0.1" required />
        </label>
        <label>
          Humidity (%)
          <input type="number" name="humidity" value={form.humidity} onChange={handleChange} min="0" max="100" step="0.1" required />
        </label>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Predicting..." : "Predict Irrigation"}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {result && (
        <div className={`prediction-result ${result.irrigate ? "irrigate-yes" : "irrigate-no"}`}>
          <div className="prediction-result-headline">
            {result.irrigate ? "💧 Irrigation Recommended" : "✅ No Irrigation Needed"}
          </div>
          {result.irrigate && (
            <div className="prediction-water-amount">
              Recommended water: <strong>{result.water_amount_liters} L</strong>
            </div>
          )}
          <div className="prediction-confidence">
            Confidence: {(result.confidence * 100).toFixed(1)}%
          </div>
          <p className="prediction-reasoning">{result.reasoning}</p>
        </div>
      )}
    </div>
  );
}

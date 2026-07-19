import React, { useState } from "react";
import { requestPrediction } from "../services/api";

export default function PredictionPanel({ latestReading, selectedDeviceId }) {
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
      // Pass the actual selected device (if one is chosen, not "All devices")
      // so the backend can look up its registered field area and scale the
      // recommendation to a real total volume, instead of just a per-m^2 figure.
      const deviceId = selectedDeviceId || "dashboard-manual";
      const data = await requestPrediction({ ...form, device_id: deviceId });
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
            <>
              {result.field_area ? (
                <div className="prediction-water-amount">
                  <div className="prediction-total-water">
                    Total for your {result.field_area.area_value} {result.field_area.area_unit}{" "}
                    field: <strong>{result.field_area.total_liters_needed.toLocaleString()} L</strong>
                  </div>
                  {result.field_area.recommended_duration_hours !== null && (
                    <div className="prediction-duration">
                      Run your irrigation system for approximately{" "}
                      <strong>{result.field_area.recommended_duration_hours} hours</strong> at its
                      rated flow rate.
                    </div>
                  )}
                  <div className="prediction-depth-note muted-text">
                    (Irrigation depth: {result.water_amount_liters} L/m² — equivalent to{" "}
                    {result.water_amount_liters}mm of water)
                  </div>
                </div>
              ) : (
                <div className="prediction-water-amount">
                  <div>
                    Recommended irrigation depth: <strong>{result.water_amount_liters} L/m²</strong>{" "}
                    <span className="muted-text">(equivalent to {result.water_amount_liters}mm)</span>
                  </div>
                  <p className="auth-tip">
                    This is a per-square-meter figure. To see the total liters needed for your
                    actual field, ask your administrator to register your field's size (and
                    optionally your irrigation system's flow rate) for this device.
                  </p>
                </div>
              )}
            </>
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

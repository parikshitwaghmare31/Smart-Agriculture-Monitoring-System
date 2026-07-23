import React, { useState } from "react";
import { requestPrediction } from "../services/api";
import { useLanguage } from "../i18n/LanguageContext";

export default function PredictionPanel({ latestReading, selectedDeviceId }) {
  const { t } = useLanguage();
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
      setError(t("predictionFailed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h3>{t("irrigationPrediction")}</h3>
        <button className="btn-secondary" onClick={useLiveReading} type="button">
          {t("useLatestReading")}
        </button>
      </div>

      <form onSubmit={handleSubmit} className="prediction-form">
        <label>
          {t("soilMoisture")} (%)
          <input type="number" name="soil_moisture" value={form.soil_moisture} onChange={handleChange} min="0" max="100" step="0.1" required />
        </label>
        <label>
          {t("temperature")} (°C)
          <input type="number" name="temperature" value={form.temperature} onChange={handleChange} min="-10" max="60" step="0.1" required />
        </label>
        <label>
          {t("humidity")} (%)
          <input type="number" name="humidity" value={form.humidity} onChange={handleChange} min="0" max="100" step="0.1" required />
        </label>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? t("predicting") : t("predictIrrigation")}
        </button>
      </form>

      {error && <p className="error-text">{error}</p>}

      {result && (
        <div className={`prediction-result ${result.irrigate ? "irrigate-yes" : "irrigate-no"}`}>
          <div className="prediction-result-headline">
            {result.irrigate ? t("irrigationRecommended") : t("noIrrigationNeeded")}
          </div>

          {result.irrigate && (
            <>
              {result.field_area ? (
                <div className="prediction-water-amount">
                  {result.field_area.zones_needed > 1 && (
                    <div className="prediction-zones-warning">
                      {t("zonesWarning")}{" "}
                      <strong>{result.field_area.zones_needed} {t("zonesShifts")}</strong>.
                    </div>
                  )}
                  <div className="prediction-total-water">
                    {t("totalForYourField")} {result.field_area.area_value} {result.field_area.area_unit}{" "}
                    {t("field")}: <strong>{result.field_area.total_liters_needed.toLocaleString()} L</strong>
                  </div>
                  {result.field_area.recommended_duration_hours !== null && (
                    <div className="prediction-duration">
                      {t("totalPumpRuntime")}{" "}
                      <strong>{result.field_area.recommended_duration_hours} {t("hours")}</strong>
                      {result.field_area.zones_needed > 1 ? t("splitAcrossZones") : ""}.
                    </div>
                  )}
                  {result.field_area.system_demand_lph && (
                    <div className="prediction-system-details">
                      {result.field_area.num_emitters?.toLocaleString()} emitters demanding{" "}
                      {result.field_area.system_demand_lph.toLocaleString()} L/hr · Pump supplies{" "}
                      {result.field_area.pump_supply_lph.toLocaleString()} L/hr
                      {result.field_area.pump_supply_is_estimated
                        ? " (estimated from HP)"
                        : ""}
                    </div>
                  )}
                  <div className="prediction-depth-note muted-text">
                    ({result.water_amount_liters} L/m² ≈ {result.water_amount_liters}mm)
                  </div>
                </div>
              ) : (
                <div className="prediction-water-amount">
                  <div>
                    <strong>{result.water_amount_liters} L/m²</strong>{" "}
                    <span className="muted-text">(≈ {result.water_amount_liters}mm)</span>
                  </div>
                  <p className="auth-tip">{t("irrigationDepthNote")}</p>
                </div>
              )}
            </>
          )}

          <div className="prediction-confidence">
            {t("confidence")}: {(result.confidence * 100).toFixed(1)}%
          </div>
          <p className="prediction-reasoning">{result.reasoning}</p>
        </div>
      )}
    </div>
  );
}

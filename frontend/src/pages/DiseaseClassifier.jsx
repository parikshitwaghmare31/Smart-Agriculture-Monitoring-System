import React, { useEffect, useState } from "react";
import { getDiseaseModelStatus, getDiseaseCrops, classifyPlantPhoto } from "../services/authApi";

export default function DiseaseClassifier({ onBack }) {
  const [modelStatus, setModelStatus] = useState(null);
  const [crops, setCrops] = useState([]);
  const [selectedCrop, setSelectedCrop] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getDiseaseModelStatus()
      .then(setModelStatus)
      .catch(() => setModelStatus({ model_loaded: false }));
    getDiseaseCrops()
      .then((data) => setCrops(data.crops || []))
      .catch(() => setCrops([]));
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setImageFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!imageFile) {
      setError("Please select or take a photo first.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const data = await classifyPlantPhoto(imageFile);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Classification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (modelStatus && !modelStatus.model_loaded) {
    return (
      <div className="dashboard">
        <div className="app-shell-nav">
          <button className="btn-secondary" onClick={onBack}>
            ← Back to Dashboard
          </button>
        </div>
        <div className="panel">
          <h2>🌿 Disease Classifier</h2>
          <div className="empty-state-banner">
            This feature isn't set up yet — no disease classifier model has been trained and
            deployed. Ask your administrator to train a model (using their own photo dataset) and
            deploy it via the Admin Panel's "Train Custom Model" tab.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="app-shell-nav">
        <button className="btn-secondary" onClick={onBack}>
          ← Back to Dashboard
        </button>
      </div>

      <div className="panel">
        <h2>🌿 Disease Classifier</h2>
        <p className="muted-text">
          Select your crop, upload or take a photo of the plant, and get an instant assessment
          plus irrigation, fertilizer, and spraying recommendations.
        </p>

        <form onSubmit={handleSubmit} className="disease-form">
          <label>
            Crop <span className="optional">(optional — helps you organize, not required for prediction)</span>
            <select value={selectedCrop} onChange={(e) => setSelectedCrop(e.target.value)}>
              <option value="">Any / Not sure</option>
              {crops.map((crop) => (
                <option key={crop} value={crop}>
                  {crop}
                </option>
              ))}
            </select>
          </label>

          <label>
            Plant Photo
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFileChange}
              required
            />
          </label>

          {previewUrl && (
            <img src={previewUrl} alt="Selected plant" className="disease-preview-image" />
          )}

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Photo"}
          </button>
        </form>

        {result && (
          <div className="disease-result">
            <div className="disease-result-header">
              <span className="disease-result-title">
                {result.crop} — {result.disease_label}
              </span>
              <span className="disease-confidence-badge">
                {(result.confidence * 100).toFixed(1)}% confidence
              </span>
            </div>

            {result.recommendation_found ? (
              <div className="disease-recommendations">
                {result.irrigation_advice && (
                  <div className="disease-rec-item">
                    <strong>💧 Irrigation:</strong> {result.irrigation_advice}
                  </div>
                )}
                {result.fertilizer_advice && (
                  <div className="disease-rec-item">
                    <strong>🌱 Fertilizer:</strong> {result.fertilizer_advice}
                  </div>
                )}
                {result.spraying_advice && (
                  <div className="disease-rec-item">
                    <strong>🧪 Spraying:</strong> {result.spraying_advice}
                  </div>
                )}
              </div>
            ) : (
              <p className="auth-tip">
                No specific recommendation has been configured for "{result.disease_label}" yet.
                Your administrator can add one via the Admin Panel, or consult a local
                agricultural expert in the meantime.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

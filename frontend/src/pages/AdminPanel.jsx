import React, { useEffect, useState, useCallback } from "react";
import { registerDevice, getAllDevices } from "../services/authApi";

export default function AdminPanel() {
  const [devices, setDevices] = useState([]);
  const [form, setForm] = useState({ device_id: "", label: "", owner_email: "", location: "" });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadDevices = useCallback(async () => {
    try {
      const data = await getAllDevices();
      setDevices(data);
    } catch (err) {
      console.error("Failed to load devices", err);
    }
  }, []);

  useEffect(() => {
    loadDevices();
  }, [loadDevices]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await registerDevice(form.device_id, form.label, form.owner_email, form.location || null);
      setSuccess(`Device "${form.device_id}" registered and assigned to ${form.owner_email}.`);
      setForm({ device_id: "", label: "", owner_email: "", location: "" });
      loadDevices();
    } catch (err) {
      const detail = err.response?.data?.detail || "Failed to register device.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-panel">
      <h2>🛠️ Admin: Manage Sensor Nodes</h2>

      <div className="panel">
        <h3>Register a New Sensor Node</h3>
        <form onSubmit={handleSubmit} className="admin-form">
          <label>
            Device ID
            <input
              type="text"
              name="device_id"
              value={form.device_id}
              onChange={handleChange}
              placeholder="e.g. esp32-field-04"
              required
            />
          </label>
          <label>
            Label
            <input
              type="text"
              name="label"
              value={form.label}
              onChange={handleChange}
              placeholder="e.g. North Field Plot A"
              required
            />
          </label>
          <label>
            Owner's Email (farmer must already be registered)
            <input
              type="email"
              name="owner_email"
              value={form.owner_email}
              onChange={handleChange}
              placeholder="farmer@example.com"
              required
            />
          </label>
          <label>
            Location <span className="optional">(optional)</span>
            <input
              type="text"
              name="location"
              value={form.location}
              onChange={handleChange}
              placeholder="e.g. Nashik, Maharashtra"
            />
          </label>

          {error && <p className="auth-error">{error}</p>}
          {success && <p className="auth-success">{success}</p>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Registering..." : "Register Device"}
          </button>
        </form>
      </div>

      <div className="panel">
        <h3>All Registered Devices ({devices.length})</h3>
        {devices.length === 0 ? (
          <p className="muted-text">No devices registered yet.</p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Device ID</th>
                <th>Label</th>
                <th>Owner</th>
                <th>Location</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((d) => (
                <tr key={d.device_id}>
                  <td>{d.device_id}</td>
                  <td>{d.label}</td>
                  <td>
                    {d.owner_name || "—"} <span className="muted-text">({d.owner_email})</span>
                  </td>
                  <td>{d.location || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

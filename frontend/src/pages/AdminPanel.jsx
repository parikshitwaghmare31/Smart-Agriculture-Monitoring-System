import React, { useEffect, useState, useCallback } from "react";
import {
  registerDevice,
  getAllDevices,
  updateDevice,
  deleteDevice,
  getAllUsers,
} from "../services/authApi";

const TABS = {
  REGISTER: "register",
  MANAGE: "manage",
  USERS: "users",
  GUIDE: "guide",
};

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState(TABS.REGISTER);

  return (
    <div className="admin-panel">
      <h2>🛠️ Admin Panel</h2>

      <div className="admin-tabs">
        <button
          className={activeTab === TABS.REGISTER ? "admin-tab active" : "admin-tab"}
          onClick={() => setActiveTab(TABS.REGISTER)}
        >
          ➕ Register Device
        </button>
        <button
          className={activeTab === TABS.MANAGE ? "admin-tab active" : "admin-tab"}
          onClick={() => setActiveTab(TABS.MANAGE)}
        >
          🔧 Manage Devices
        </button>
        <button
          className={activeTab === TABS.USERS ? "admin-tab active" : "admin-tab"}
          onClick={() => setActiveTab(TABS.USERS)}
        >
          👥 User Management
        </button>
        <button
          className={activeTab === TABS.GUIDE ? "admin-tab active" : "admin-tab"}
          onClick={() => setActiveTab(TABS.GUIDE)}
        >
          📘 ESP32 Setup Guide
        </button>
      </div>

      {activeTab === TABS.REGISTER && <RegisterDeviceTab />}
      {activeTab === TABS.MANAGE && <ManageDevicesTab />}
      {activeTab === TABS.USERS && <UserManagementTab />}
      {activeTab === TABS.GUIDE && <Esp32GuideTab />}
    </div>
  );
}

function RegisterDeviceTab() {
  const [form, setForm] = useState({ device_id: "", label: "", owner_email: "", location: "" });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);

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
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to register device.");
    } finally {
      setLoading(false);
    }
  };

  return (
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
  );
}

function ManageDevicesTab() {
  const [devices, setDevices] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ label: "", owner_email: "", location: "" });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadDevices = useCallback(async () => {
    try {
      const data = await getAllDevices();
      setDevices(data);
    } catch (err) {
      setError("Failed to load devices.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDevices();
  }, [loadDevices]);

  const startEditing = (device) => {
    setEditingId(device.device_id);
    setEditForm({
      label: device.label || "",
      owner_email: device.owner_email || "",
      location: device.location || "",
    });
    setError(null);
  };

  const cancelEditing = () => {
    setEditingId(null);
    setError(null);
  };

  const saveEditing = async (deviceId) => {
    try {
      await updateDevice(deviceId, editForm);
      setEditingId(null);
      loadDevices();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update device.");
    }
  };

  const handleDelete = async (deviceId) => {
    if (!window.confirm(`Unregister "${deviceId}"? Historical readings are kept, but the farmer will no longer see it.`)) {
      return;
    }
    try {
      await deleteDevice(deviceId);
      loadDevices();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete device.");
    }
  };

  if (loading) return <div className="panel">Loading devices...</div>;

  return (
    <div className="panel">
      <h3>Manage Registered Devices ({devices.length})</h3>
      {error && <p className="auth-error">{error}</p>}
      {devices.length === 0 ? (
        <p className="muted-text">No devices registered yet.</p>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>Device ID</th>
              <th>Label</th>
              <th>Owner Email</th>
              <th>Location</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.device_id}>
                <td>{d.device_id}</td>
                {editingId === d.device_id ? (
                  <>
                    <td>
                      <input
                        className="inline-edit-input"
                        value={editForm.label}
                        onChange={(e) => setEditForm({ ...editForm, label: e.target.value })}
                      />
                    </td>
                    <td>
                      <input
                        className="inline-edit-input"
                        value={editForm.owner_email}
                        onChange={(e) => setEditForm({ ...editForm, owner_email: e.target.value })}
                      />
                    </td>
                    <td>
                      <input
                        className="inline-edit-input"
                        value={editForm.location}
                        onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
                      />
                    </td>
                    <td className="admin-table-actions">
                      <button className="btn-secondary" onClick={() => saveEditing(d.device_id)}>
                        Save
                      </button>
                      <button className="btn-secondary" onClick={cancelEditing}>
                        Cancel
                      </button>
                    </td>
                  </>
                ) : (
                  <>
                    <td>{d.label}</td>
                    <td>
                      {d.owner_name || "—"} <span className="muted-text">({d.owner_email})</span>
                    </td>
                    <td>{d.location || "—"}</td>
                    <td className="admin-table-actions">
                      <button className="btn-secondary" onClick={() => startEditing(d)}>
                        Edit
                      </button>
                      <button className="btn-danger" onClick={() => handleDelete(d.device_id)}>
                        Delete
                      </button>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function UserManagementTab() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAllUsers()
      .then(setUsers)
      .catch(() => setError("Failed to load users."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="panel">Loading users...</div>;

  return (
    <div className="panel">
      <h3>Registered Users ({users.length})</h3>
      {error && <p className="auth-error">{error}</p>}
      <table className="admin-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Devices Owned</th>
            <th>Joined</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.email}>
              <td>{u.full_name}</td>
              <td>{u.email}</td>
              <td>
                <span className={u.role === "admin" ? "role-badge admin" : "role-badge farmer"}>
                  {u.role}
                </span>
              </td>
              <td>{u.device_count}</td>
              <td>{new Date(u.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Esp32GuideTab() {
  return (
    <div className="panel">
      <h3>📘 Configuring a Real ESP32 Sensor Node</h3>
      <p className="muted-text">
        Follow these steps to get a physical ESP32 board sending live data to this dashboard.
        The firmware file lives at <code>mqtt-simulator/esp32_sketch.ino</code> in the project repo.
      </p>

      <ol className="setup-guide-steps">
        <li>
          <strong>Wire the sensors:</strong> soil moisture sensor analog output → GPIO 34;
          DHT22 data pin → GPIO 4; both sensors powered from 3.3V/GND.
        </li>
        <li>
          <strong>Install Arduino IDE</strong> with ESP32 board support (Boards Manager → search
          "esp32" by Espressif Systems), plus 3 libraries via Library Manager:
          <code>PubSubClient</code>, <code>DHT sensor library</code> (Adafruit), <code>ArduinoJson</code>.
        </li>
        <li>
          <strong>Open <code>esp32_sketch.ino</code></strong> and edit these values at the top:
          <ul>
            <li><code>WIFI_SSID</code> / <code>WIFI_PASSWORD</code> — your WiFi network</li>
            <li><code>MQTT_PASSWORD</code> — the current EMQX Cloud broker password</li>
            <li>
              <code>DEVICE_ID</code> — a unique identifier for this exact board, e.g.{" "}
              <code>esp32-field-05</code>. Every physical unit needs a different ID.
            </li>
          </ul>
        </li>
        <li>
          <strong>Calibrate the soil sensor:</strong> upload the sketch, open the Serial Monitor,
          test the sensor in dry air and then in water, and adjust <code>SOIL_DRY_RAW</code> /
          <code>SOIL_WET_RAW</code> to match the raw values you observe.
        </li>
        <li>
          <strong>Upload and power on</strong> — the Serial Monitor should show{" "}
          <code>"Published: {'{'}...{'}'}"</code> every 5 seconds once connected.
        </li>
        <li>
          <strong>Register the device here in the Admin Panel:</strong> go to "Register Device",
          enter the same <code>DEVICE_ID</code> you set in the sketch, a friendly label, and the
          email of the farmer who should see this field's data. It'll appear on their dashboard
          immediately (showing "no data yet" until the board actually starts publishing).
        </li>
      </ol>

      <p className="auth-tip">
        Multiple boards on one farm just need different <code>DEVICE_ID</code> values — everything
        else (WiFi, broker, credentials) can stay the same across all of them.
      </p>
    </div>
  );
}

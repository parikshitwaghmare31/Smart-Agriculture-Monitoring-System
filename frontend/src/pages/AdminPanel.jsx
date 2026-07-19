import React, { useEffect, useState, useCallback } from "react";
import {
  registerDevice,
  getAllDevices,
  updateDevice,
  deleteDevice,
  getAllUsers,
  updateUser,
  deleteUser,
  getDiseaseModelStatus,
  getDiseaseClasses,
  createDiseaseClass,
  updateDiseaseClass,
  deleteDiseaseClass,
  deployDiseaseModel,
} from "../services/authApi";

const TABS = {
  REGISTER: "register",
  MANAGE: "manage",
  USERS: "users",
  GUIDE: "guide",
  RECOMMENDATIONS: "recommendations",
  TRAIN_MODEL: "train_model",
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
        <button
          className={activeTab === TABS.RECOMMENDATIONS ? "admin-tab active" : "admin-tab"}
          onClick={() => setActiveTab(TABS.RECOMMENDATIONS)}
        >
          🩺 Recommendation Rules
        </button>
        <button
          className={activeTab === TABS.TRAIN_MODEL ? "admin-tab active" : "admin-tab"}
          onClick={() => setActiveTab(TABS.TRAIN_MODEL)}
        >
          🧠 Train Custom Model
        </button>
      </div>

      {activeTab === TABS.REGISTER && <RegisterDeviceTab />}
      {activeTab === TABS.MANAGE && <ManageDevicesTab />}
      {activeTab === TABS.USERS && <UserManagementTab />}
      {activeTab === TABS.GUIDE && <Esp32GuideTab />}
      {activeTab === TABS.RECOMMENDATIONS && <RecommendationRulesTab />}
      {activeTab === TABS.TRAIN_MODEL && <TrainCustomModelTab />}
    </div>
  );
}

function RegisterDeviceTab() {
  const [form, setForm] = useState({
    device_id: "",
    label: "",
    owner_email: "",
    location: "",
    area_value: "",
    area_unit: "acre",
    flow_rate_lph: "",
  });
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
      await registerDevice(
        form.device_id,
        form.label,
        form.owner_email,
        form.location || null,
        form.area_value ? parseFloat(form.area_value) : null,
        form.area_unit,
        form.flow_rate_lph ? parseFloat(form.flow_rate_lph) : null
      );
      setSuccess(`Device "${form.device_id}" registered and assigned to ${form.owner_email}.`);
      setForm({
        device_id: "",
        label: "",
        owner_email: "",
        location: "",
        area_value: "",
        area_unit: "acre",
        flow_rate_lph: "",
      });
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

        <div className="admin-form-row">
          <label>
            Field Size <span className="optional">(optional, enables total water calc)</span>
            <input
              type="number"
              step="0.01"
              min="0"
              name="area_value"
              value={form.area_value}
              onChange={handleChange}
              placeholder="e.g. 1"
            />
          </label>
          <label>
            Unit
            <select name="area_unit" value={form.area_unit} onChange={handleChange}>
              <option value="acre">Acre</option>
              <option value="hectare">Hectare</option>
              <option value="square_meter">Square Meter</option>
              <option value="square_feet">Square Feet</option>
            </select>
          </label>
        </div>

        <label>
          Irrigation System Flow Rate (L/hour) <span className="optional">(optional, enables duration estimate)</span>
          <input
            type="number"
            step="0.1"
            min="0"
            name="flow_rate_lph"
            value={form.flow_rate_lph}
            onChange={handleChange}
            placeholder="e.g. 4000 (check your drip/sprinkler system's rated flow rate)"
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
  const [editForm, setEditForm] = useState({
    label: "",
    owner_email: "",
    location: "",
    area_value: "",
    area_unit: "acre",
    flow_rate_lph: "",
  });
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
      area_value: device.area_value ?? "",
      area_unit: device.area_unit || "acre",
      flow_rate_lph: device.flow_rate_lph ?? "",
    });
    setError(null);
  };

  const cancelEditing = () => {
    setEditingId(null);
    setError(null);
  };

  const saveEditing = async (deviceId) => {
    try {
      const payload = {
        ...editForm,
        area_value: editForm.area_value !== "" ? parseFloat(editForm.area_value) : null,
        flow_rate_lph: editForm.flow_rate_lph !== "" ? parseFloat(editForm.flow_rate_lph) : null,
      };
      await updateDevice(deviceId, payload);
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
              <th>Field Area</th>
              <th>Flow Rate (L/hr)</th>
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
                    <td>
                      <div className="inline-edit-area-group">
                        <input
                          className="inline-edit-input"
                          type="number"
                          step="0.01"
                          placeholder="size"
                          value={editForm.area_value}
                          onChange={(e) => setEditForm({ ...editForm, area_value: e.target.value })}
                        />
                        <select
                          className="inline-edit-input"
                          value={editForm.area_unit}
                          onChange={(e) => setEditForm({ ...editForm, area_unit: e.target.value })}
                        >
                          <option value="acre">acre</option>
                          <option value="hectare">hectare</option>
                          <option value="square_meter">m²</option>
                          <option value="square_feet">ft²</option>
                        </select>
                      </div>
                    </td>
                    <td>
                      <input
                        className="inline-edit-input"
                        type="number"
                        step="0.1"
                        value={editForm.flow_rate_lph}
                        onChange={(e) => setEditForm({ ...editForm, flow_rate_lph: e.target.value })}
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
                    <td>
                      {d.area_value ? `${d.area_value} ${d.area_unit === "square_meter" ? "m²" : d.area_unit === "square_feet" ? "ft²" : d.area_unit}` : "—"}
                    </td>
                    <td>{d.flow_rate_lph ? `${d.flow_rate_lph} L/hr` : "—"}</td>
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
      <p className="muted-text" style={{ marginTop: "10px" }}>
        Setting a field area enables the irrigation prediction to show total liters needed for
        the whole field, not just a per-square-meter figure. Adding a flow rate also estimates
        how long to run the irrigation system.
      </p>
    </div>
  );
}

function UserManagementTab() {
  const [users, setUsers] = useState([]);
  const [editingEmail, setEditingEmail] = useState(null);
  const [editForm, setEditForm] = useState({ full_name: "", role: "farmer", new_password: "" });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUsers = useCallback(async () => {
    try {
      const data = await getAllUsers();
      setUsers(data);
    } catch (err) {
      setError("Failed to load users.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const startEditing = (user) => {
    setEditingEmail(user.email);
    setEditForm({ full_name: user.full_name, role: user.role, new_password: "" });
    setError(null);
  };

  const cancelEditing = () => {
    setEditingEmail(null);
    setError(null);
  };

  const saveEditing = async (email) => {
    setError(null);
    const updates = { full_name: editForm.full_name, role: editForm.role };
    if (editForm.new_password) {
      updates.new_password = editForm.new_password;
    }
    try {
      await updateUser(email, updates);
      setEditingEmail(null);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update user.");
    }
  };

  const handleDelete = async (user) => {
    if (
      !window.confirm(
        `Delete the account for ${user.full_name} (${user.email})? This cannot be undone.`
      )
    ) {
      return;
    }
    setError(null);
    try {
      await deleteUser(user.email);
      loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete user.");
    }
  };

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
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.email}>
              {editingEmail === u.email ? (
                <>
                  <td>
                    <input
                      className="inline-edit-input"
                      value={editForm.full_name}
                      onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                    />
                  </td>
                  <td>{u.email}</td>
                  <td>
                    <select
                      className="inline-edit-input"
                      value={editForm.role}
                      onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                    >
                      <option value="farmer">farmer</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td>{u.device_count}</td>
                  <td>
                    <input
                      className="inline-edit-input"
                      type="password"
                      placeholder="Reset password (optional)"
                      value={editForm.new_password}
                      onChange={(e) => setEditForm({ ...editForm, new_password: e.target.value })}
                    />
                  </td>
                  <td className="admin-table-actions">
                    <button className="btn-secondary" onClick={() => saveEditing(u.email)}>
                      Save
                    </button>
                    <button className="btn-secondary" onClick={cancelEditing}>
                      Cancel
                    </button>
                  </td>
                </>
              ) : (
                <>
                  <td>{u.full_name}</td>
                  <td>{u.email}</td>
                  <td>
                    <span className={u.role === "admin" ? "role-badge admin" : "role-badge farmer"}>
                      {u.role}
                    </span>
                  </td>
                  <td>{u.device_count}</td>
                  <td>{new Date(u.created_at).toLocaleDateString()}</td>
                  <td className="admin-table-actions">
                    <button className="btn-secondary" onClick={() => startEditing(u)}>
                      Edit
                    </button>
                    <button className="btn-danger" onClick={() => handleDelete(u)}>
                      Delete
                    </button>
                  </td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted-text" style={{ marginTop: "10px" }}>
        Note: a user can't be deleted while they still own devices (reassign or delete those
        first), and the last remaining admin account can't be demoted or deleted.
      </p>
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

function RecommendationRulesTab() {
  const [classes, setClasses] = useState([]);
  const [form, setForm] = useState({
    crop: "",
    disease_label: "",
    irrigation_advice: "",
    fertilizer_advice: "",
    spraying_advice: "",
  });
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadClasses = useCallback(async () => {
    try {
      const data = await getDiseaseClasses();
      setClasses(data);
    } catch (err) {
      setError("Failed to load recommendation rules.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadClasses();
  }, [loadClasses]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      await createDiseaseClass(form);
      setSuccess(`Recommendation for ${form.crop} / ${form.disease_label} added.`);
      setForm({
        crop: "",
        disease_label: "",
        irrigation_advice: "",
        fertilizer_advice: "",
        spraying_advice: "",
      });
      loadClasses();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to add recommendation.");
    }
  };

  const startEditing = (item) => {
    setEditingId(item.id);
    setEditForm({
      irrigation_advice: item.irrigation_advice,
      fertilizer_advice: item.fertilizer_advice,
      spraying_advice: item.spraying_advice,
    });
  };

  const saveEditing = async (id) => {
    try {
      await updateDiseaseClass(id, editForm);
      setEditingId(null);
      loadClasses();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update recommendation.");
    }
  };

  const handleDelete = async (item) => {
    if (!window.confirm(`Delete the recommendation for ${item.crop} / ${item.disease_label}?`)) {
      return;
    }
    try {
      await deleteDiseaseClass(item.id);
      loadClasses();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete recommendation.");
    }
  };

  if (loading) return <div className="panel">Loading recommendation rules...</div>;

  return (
    <>
      <div className="panel">
        <h3>Add a Recommendation Rule</h3>
        <p className="muted-text">
          These define what a farmer sees after the disease classifier identifies a condition.
          The "crop" and "disease label" here should exactly match the class names your trained
          model uses (see the Train Custom Model tab).
        </p>
        <form onSubmit={handleCreate} className="admin-form">
          <label>
            Crop
            <input
              type="text"
              name="crop"
              value={form.crop}
              onChange={handleChange}
              placeholder="e.g. Tomato"
              required
            />
          </label>
          <label>
            Disease Label
            <input
              type="text"
              name="disease_label"
              value={form.disease_label}
              onChange={handleChange}
              placeholder="e.g. Early Blight (or 'Healthy')"
              required
            />
          </label>
          <label>
            Irrigation Advice
            <input
              type="text"
              name="irrigation_advice"
              value={form.irrigation_advice}
              onChange={handleChange}
              placeholder="e.g. Reduce watering frequency, avoid overhead irrigation"
              required
            />
          </label>
          <label>
            Fertilizer Advice
            <input
              type="text"
              name="fertilizer_advice"
              value={form.fertilizer_advice}
              onChange={handleChange}
              placeholder="e.g. Apply balanced NPK, avoid excess nitrogen"
              required
            />
          </label>
          <label>
            Spraying Advice
            <input
              type="text"
              name="spraying_advice"
              value={form.spraying_advice}
              onChange={handleChange}
              placeholder="e.g. Apply copper-based fungicide every 7-10 days"
              required
            />
          </label>

          {error && <p className="auth-error">{error}</p>}
          {success && <p className="auth-success">{success}</p>}

          <button type="submit" className="btn-primary">
            Add Recommendation
          </button>
        </form>
      </div>

      <div className="panel">
        <h3>Existing Recommendations ({classes.length})</h3>
        {classes.length === 0 ? (
          <p className="muted-text">No recommendation rules configured yet.</p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Crop</th>
                <th>Disease</th>
                <th>Irrigation</th>
                <th>Fertilizer</th>
                <th>Spraying</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {classes.map((c) => (
                <tr key={c.id}>
                  <td>{c.crop}</td>
                  <td>{c.disease_label}</td>
                  {editingId === c.id ? (
                    <>
                      <td>
                        <input
                          className="inline-edit-input"
                          value={editForm.irrigation_advice}
                          onChange={(e) =>
                            setEditForm({ ...editForm, irrigation_advice: e.target.value })
                          }
                        />
                      </td>
                      <td>
                        <input
                          className="inline-edit-input"
                          value={editForm.fertilizer_advice}
                          onChange={(e) =>
                            setEditForm({ ...editForm, fertilizer_advice: e.target.value })
                          }
                        />
                      </td>
                      <td>
                        <input
                          className="inline-edit-input"
                          value={editForm.spraying_advice}
                          onChange={(e) =>
                            setEditForm({ ...editForm, spraying_advice: e.target.value })
                          }
                        />
                      </td>
                      <td className="admin-table-actions">
                        <button className="btn-secondary" onClick={() => saveEditing(c.id)}>
                          Save
                        </button>
                        <button className="btn-secondary" onClick={() => setEditingId(null)}>
                          Cancel
                        </button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td>{c.irrigation_advice}</td>
                      <td>{c.fertilizer_advice}</td>
                      <td>{c.spraying_advice}</td>
                      <td className="admin-table-actions">
                        <button className="btn-secondary" onClick={() => startEditing(c)}>
                          Edit
                        </button>
                        <button className="btn-danger" onClick={() => handleDelete(c)}>
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
    </>
  );
}

function TrainCustomModelTab() {
  const [status, setStatus] = useState(null);
  const [modelFile, setModelFile] = useState(null);
  const [classNamesFile, setClassNamesFile] = useState(null);
  const [reportFile, setReportFile] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadStatus = useCallback(() => {
    getDiseaseModelStatus()
      .then(setStatus)
      .catch(() => setStatus({ model_loaded: false }));
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const handleDeploy = async (e) => {
    e.preventDefault();
    if (!modelFile || !classNamesFile) {
      setError("Both model.onnx and class_names.json are required.");
      return;
    }
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      const data = await deployDiseaseModel(modelFile, classNamesFile, reportFile);
      setSuccess(`Model deployed successfully — ${data.num_classes} classes now active.`);
      loadStatus();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to deploy model.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h3>🧠 Train Your Own Disease Classifier</h3>
      <p className="muted-text">
        Training happens on your own machine (not on this server) — TensorFlow's memory
        footprint would exceed this app's hosting limits. The workflow:
      </p>

      <ol className="setup-guide-steps">
        <li>
          <strong>Collect labeled photos.</strong> Organize them into folders named{" "}
          <code>Crop__DiseaseLabel</code> (e.g. <code>Tomato__Early_Blight</code>,{" "}
          <code>Tomato__Healthy</code>). A public dataset like PlantVillage (Kaggle) works well.
        </li>
        <li>
          <strong>Don't have labeled photos yet?</strong> Use{" "}
          <code>ml/disease_classifier/scripts/cluster_unlabeled_images.py</code> first — it
          groups similar-looking raw photos together automatically (unsupervised), so you only
          need to label whole groups instead of every photo individually.
        </li>
        <li>
          <strong>Train:</strong> on your own machine, run:
          <br />
          <code>
            pip install -r ml/disease_classifier/requirements-training.txt
            <br />
            python ml/disease_classifier/scripts/train_classifier.py --data-dir /path/to/dataset
          </code>
        </li>
        <li>
          <strong>Deploy:</strong> upload the resulting <code>model.onnx</code> and{" "}
          <code>class_names.json</code> below (plus <code>training_report.json</code>{" "}
          optionally, for your own reference). The new model activates immediately — no restart
          needed.
        </li>
        <li>
          <strong>Add recommendations:</strong> go to the "Recommendation Rules" tab and add
          irrigation/fertilizer/spraying advice for each crop+disease combination your model
          recognizes.
        </li>
      </ol>

      <div className="disease-model-status">
        {status?.model_loaded ? (
          <>
            <p className="auth-success">
              ✅ A model is currently deployed with {status.num_classes} classes:{" "}
              {status.classes.map((c) => `${c.crop}/${c.disease_label}`).join(", ")}
            </p>
            {status.training_report && (
              <p className="muted-text">
                Training report: validation accuracy{" "}
                {(status.training_report.phase2_final_val_accuracy * 100).toFixed(1)}% on{" "}
                {status.training_report.num_classes} classes.
              </p>
            )}
          </>
        ) : (
          <p className="empty-state-banner">No model deployed yet. Upload one below to get started.</p>
        )}
      </div>

      <form onSubmit={handleDeploy} className="admin-form">
        <label>
          model.onnx
          <input
            type="file"
            accept=".onnx"
            onChange={(e) => setModelFile(e.target.files[0])}
            required
          />
        </label>
        <label>
          class_names.json
          <input
            type="file"
            accept=".json"
            onChange={(e) => setClassNamesFile(e.target.files[0])}
            required
          />
        </label>
        <label>
          training_report.json <span className="optional">(optional)</span>
          <input
            type="file"
            accept=".json"
            onChange={(e) => setReportFile(e.target.files[0])}
          />
        </label>

        {error && <p className="auth-error">{error}</p>}
        {success && <p className="auth-success">{success}</p>}

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Deploying..." : "Deploy Model"}
        </button>
      </form>
    </div>
  );
}

import React from "react";

export default function DeviceSelector({ devices, selectedDeviceId, onSelect }) {
  return (
    <div className="device-selector">
      <label htmlFor="device-select">Field / Device:</label>
      <select
        id="device-select"
        value={selectedDeviceId || "all"}
        onChange={(e) => onSelect(e.target.value === "all" ? null : e.target.value)}
      >
        <option value="all">All devices</option>
        {devices.map((d) => (
          <option key={d.device_id} value={d.device_id}>
            {d.label ? `${d.label} (${d.device_id})` : d.device_id}
            {!d.has_data ? " — no data yet" : ""}
          </option>
        ))}
      </select>
    </div>
  );
}


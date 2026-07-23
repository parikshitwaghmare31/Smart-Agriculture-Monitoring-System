import React from "react";
import { useLanguage } from "../i18n/LanguageContext";

export default function DeviceSelector({ devices, selectedDeviceId, onSelect }) {
  const { t } = useLanguage();
  return (
    <div className="device-selector">
      <label htmlFor="device-select">{t("fieldDevice")}</label>
      <select
        id="device-select"
        value={selectedDeviceId || "all"}
        onChange={(e) => onSelect(e.target.value === "all" ? null : e.target.value)}
      >
        <option value="all">{t("allDevices")}</option>
        {devices.map((d) => (
          <option key={d.device_id} value={d.device_id}>
            {d.label ? `${d.label} (${d.device_id})` : d.device_id}
            {!d.has_data ? ` — ${t("noDataYet")}` : ""}
          </option>
        ))}
      </select>
    </div>
  );
}

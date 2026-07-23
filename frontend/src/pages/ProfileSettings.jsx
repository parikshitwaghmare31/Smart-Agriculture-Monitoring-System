import React, { useState, useEffect } from "react";
import { getMyProfile, updateMyProfile } from "../services/authApi";
import { useLanguage } from "../i18n/LanguageContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function ProfileSettings({ onBack, onProfileUpdated }) {
  const { t } = useLanguage();
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({
    phone_number: "",
    alerts_enabled: false,
    alert_channel: "sms",
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMyProfile()
      .then((data) => {
        setProfile(data);
        setForm({
          phone_number: data.phone_number || "",
          alerts_enabled: data.alerts_enabled || false,
          alert_channel: data.alert_channel || "sms",
        });
      })
      .catch(() => setError("Failed to load profile."))
      .finally(() => setLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (form.alerts_enabled && !form.phone_number) {
      setError(t("phoneRequiredForAlerts"));
      return;
    }

    setSaving(true);
    try {
      const updated = await updateMyProfile(form);
      setSuccess(t("profileUpdated"));
      if (onProfileUpdated) onProfileUpdated(updated);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="panel">Loading...</div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="app-shell-nav">
        <button className="btn-secondary" onClick={onBack}>
          {t("backToDashboard")}
        </button>
      </div>

      <div className="panel">
        <h2>⚙️ {t("profileSettings")}</h2>
        <p className="muted-text">
          {profile?.full_name} ({profile?.email})
        </p>

        <div className="profile-language-section">
          <strong>{t("language")}:</strong> <LanguageSwitcher />
        </div>

        <form onSubmit={handleSubmit} className="admin-form">
          <label>
            {t("phoneNumber")}
            <input
              type="tel"
              value={form.phone_number}
              onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
              placeholder="+919876543210"
            />
          </label>

          <h3 className="profile-section-title">{t("alertPreferences")}</h3>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={form.alerts_enabled}
              onChange={(e) => setForm({ ...form, alerts_enabled: e.target.checked })}
            />
            {t("enableAlerts")}
          </label>

          {form.alerts_enabled && (
            <label>
              {t("alertChannel")}
              <select
                value={form.alert_channel}
                onChange={(e) => setForm({ ...form, alert_channel: e.target.value })}
              >
                <option value="sms">{t("sms")}</option>
                <option value="whatsapp">{t("whatsapp")}</option>
                <option value="both">{t("both")}</option>
              </select>
            </label>
          )}

          {error && <p className="auth-error">{error}</p>}
          {success && <p className="auth-success">{success}</p>}

          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? t("saving") : t("saveChanges")}
          </button>
        </form>
      </div>
    </div>
  );
}

import React, { useState } from "react";
import { registerFarmer } from "../services/authApi";
import { useLanguage } from "../i18n/LanguageContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function Register({ onRegisterSuccess, onSwitchToLogin }) {
  const { t } = useLanguage();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await registerFarmer(email, password, fullName, phoneNumber);
      setSuccess(true);
    } catch (err) {
      const detail = err.response?.data?.detail || "Registration failed. Please try again.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h1>🌱 Smart Agriculture</h1>
          <h2>{t("registerTitle")}</h2>
          <p className="auth-success">{t("registrationSuccess")}</p>
          <p className="auth-tip">{t("registrationDeviceNote")} ({email})</p>
          <button type="button" className="btn-primary" onClick={onSwitchToLogin}>
            {t("backToLogin")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-language-switcher">
          <LanguageSwitcher />
        </div>
        <h1>🌱 Smart Agriculture</h1>
        <h2>{t("registerTitle")}</h2>
        <p className="muted-text">{t("registerSubtitle")}</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            {t("fullName")}
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              autoComplete="name"
            />
          </label>
          <label>
            {t("email")}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>
          <label>
            {t("password")}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
            />
          </label>
          <label>
            {t("phoneNumber")} <span className="optional">({t("phoneNumberHint")})</span>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+919876543210"
              autoComplete="tel"
            />
          </label>

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? t("creatingAccount") : t("createAccount")}
          </button>
        </form>

        <p className="auth-switch">
          {t("alreadyHaveAccount")}{" "}
          <button type="button" className="link-button" onClick={onSwitchToLogin}>
            {t("backToLogin")}
          </button>
        </p>
      </div>
    </div>
  );
}

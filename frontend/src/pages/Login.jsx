import React, { useState } from "react";
import { login } from "../services/authApi";
import { useLanguage } from "../i18n/LanguageContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function Login({ onLoginSuccess, onSwitchToRegister }) {
  const { t, setLanguage } = useLanguage();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await login(email, password);
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      // Sync the dashboard's language to whatever this account has saved,
      // so a farmer who set Marathi previously sees it immediately again.
      if (data.user?.preferred_language) {
        setLanguage(data.user.preferred_language);
      }
      onLoginSuccess(data.user);
    } catch (err) {
      const detail = err.response?.data?.detail || "Login failed. Check your credentials.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-language-switcher">
          <LanguageSwitcher />
        </div>
        <h1>🌱 Smart Agriculture</h1>
        <h2>{t("loginTitle")}</h2>

        <form onSubmit={handleSubmit} className="auth-form">
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
              autoComplete="current-password"
            />
          </label>

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? t("signingIn") : t("signIn")}
          </button>
        </form>

        <p className="auth-switch">
          {t("noAccountYet")}{" "}
          <button type="button" className="link-button" onClick={onSwitchToRegister}>
            {t("registerAsFarmer")}
          </button>
        </p>
      </div>
    </div>
  );
}

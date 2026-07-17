import React, { useState } from "react";
import { registerFarmer } from "../services/authApi";

export default function Register({ onRegisterSuccess, onSwitchToLogin }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await registerFarmer(email, password, fullName);
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
          <h2>Account Created!</h2>
          <p className="auth-success">
            Your farmer account has been created. You can now sign in.
          </p>
          <p className="auth-tip">
            Once signed in, ask your system administrator to register your sensor
            node(s) and link them to your account ({email}) so you can start
            viewing your field's live data.
          </p>
          <button type="button" className="btn-primary" onClick={onSwitchToLogin}>
            Go to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>🌱 Smart Agriculture</h1>
        <h2>Farmer Registration</h2>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Full Name
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              autoComplete="name"
            />
          </label>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
            />
          </label>

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account?{" "}
          <button type="button" className="link-button" onClick={onSwitchToLogin}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}

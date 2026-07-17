import React, { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import AdminPanel from "./pages/AdminPanel";
import "./App.css";

// View names, kept simple and explicit rather than pulling in a router
// library for what is currently just 4 screens.
const VIEWS = {
  LOGIN: "login",
  REGISTER: "register",
  DASHBOARD: "dashboard",
  ADMIN: "admin",
};

export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState(VIEWS.LOGIN);
  const [checkedStorage, setCheckedStorage] = useState(false);

  // On first load, restore session from localStorage if a token/user was saved.
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const storedToken = localStorage.getItem("access_token");
    if (storedUser && storedToken) {
      try {
        setUser(JSON.parse(storedUser));
        setView(VIEWS.DASHBOARD);
      } catch {
        localStorage.removeItem("user");
        localStorage.removeItem("access_token");
      }
    }
    setCheckedStorage(true);
  }, []);

  const handleLoginSuccess = (loggedInUser) => {
    setUser(loggedInUser);
    setView(VIEWS.DASHBOARD);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setUser(null);
    setView(VIEWS.LOGIN);
  };

  // Avoid a flash of the login screen while we check localStorage on first render.
  if (!checkedStorage) {
    return null;
  }

  if (view === VIEWS.LOGIN) {
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onSwitchToRegister={() => setView(VIEWS.REGISTER)}
      />
    );
  }

  if (view === VIEWS.REGISTER) {
    return <Register onSwitchToLogin={() => setView(VIEWS.LOGIN)} />;
  }

  if (view === VIEWS.ADMIN) {
    return (
      <div className="app-shell">
        <div className="app-shell-nav">
          <button className="btn-secondary" onClick={() => setView(VIEWS.DASHBOARD)}>
            ← Back to Dashboard
          </button>
        </div>
        <AdminPanel />
      </div>
    );
  }

  return (
    <Dashboard
      user={user}
      onLogout={handleLogout}
      onOpenAdminPanel={() => setView(VIEWS.ADMIN)}
    />
  );
}

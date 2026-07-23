import React, { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import AdminPanel from "./pages/AdminPanel";
import DiseaseClassifier from "./pages/DiseaseClassifier";
import ProfileSettings from "./pages/ProfileSettings";
import { useLanguage } from "./i18n/LanguageContext";
import "./App.css";

// View names, kept simple and explicit rather than pulling in a router
// library for what is currently just 6 screens.
const VIEWS = {
  LOGIN: "login",
  REGISTER: "register",
  DASHBOARD: "dashboard",
  ADMIN: "admin",
  DISEASE_CLASSIFIER: "disease_classifier",
  PROFILE: "profile",
};

export default function App() {
  const { setLanguage } = useLanguage();
  const [user, setUser] = useState(null);
  const [view, setView] = useState(VIEWS.LOGIN);
  const [checkedStorage, setCheckedStorage] = useState(false);

  // On first load, restore session from localStorage if a token/user was saved.
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const storedToken = localStorage.getItem("access_token");
    if (storedUser && storedToken) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        if (parsedUser?.preferred_language) {
          setLanguage(parsedUser.preferred_language);
        }
        setView(VIEWS.DASHBOARD);
      } catch {
        localStorage.removeItem("user");
        localStorage.removeItem("access_token");
      }
    }
    setCheckedStorage(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const handleProfileUpdated = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem("user", JSON.stringify(updatedUser));
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

  if (view === VIEWS.DISEASE_CLASSIFIER) {
    return <DiseaseClassifier onBack={() => setView(VIEWS.DASHBOARD)} />;
  }

  if (view === VIEWS.PROFILE) {
    return (
      <ProfileSettings
        onBack={() => setView(VIEWS.DASHBOARD)}
        onProfileUpdated={handleProfileUpdated}
      />
    );
  }

  return (
    <Dashboard
      user={user}
      onLogout={handleLogout}
      onOpenAdminPanel={() => setView(VIEWS.ADMIN)}
      onOpenDiseaseClassifier={() => setView(VIEWS.DISEASE_CLASSIFIER)}
      onOpenProfile={() => setView(VIEWS.PROFILE)}
    />
  );
}

import { Outlet, useNavigate, NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { signOut } from "firebase/auth";
import { auth } from "../firebase/config";
import "./LayoutPage.css";

function LayoutPage() {
  const [hasNewAlerts, setHasNewAlerts] = useState(false);

useEffect(() => {
  const checkAlerts = () => {
    const flag = localStorage.getItem("hasNewAlerts");
    setHasNewAlerts(flag === "true");
  };

  checkAlerts();

  const interval = setInterval(checkAlerts, 2000);

  return () => clearInterval(interval);
}, []);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await signOut(auth);
    navigate("/");
  };

  return (
    <div>
      {/* 🔥 NAVBAR */}
      <nav className="navbar">
  <h2 className="logo">MediaShield-AI</h2>
  <div className="nav-links">
  <NavLink
    to="/app/dashboard"
    className={({ isActive }) => isActive ? "active-link" : ""}
  >
    Dashboard
  </NavLink>

  <NavLink
    to="/app/upload"
    className={({ isActive }) => isActive ? "active-link" : ""}
  >
    Upload
  </NavLink>

  <NavLink
  to="/app/alerts"
  className={({ isActive }) => isActive ? "active-link nav-alert" : "nav-alert"}
>
  Alerts
  {hasNewAlerts && <span className="alert-dot"></span>}
</NavLink>
</div>

  <button className="logout-btn" onClick={handleLogout}>
    Logout
  </button>
</nav>

      {/* 🔥 PAGE CONTENT */}
      <div style={{ padding: "20px" }}>
        <Outlet />
      </div>
    </div>
  );
}

export default LayoutPage;
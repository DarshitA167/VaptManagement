import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../styles/Navbar.css";
import { Menu } from "lucide-react";

import HomeIcon from "../assets/HomeIcon.png";
import PhysicalIcon from "../assets/PhysicalIcon.png";
import MentalIcon from "../assets/MentalIcon.png";
import PasswordIcon from "../assets/PasswordIcon.png";
import CyberIcon from "../assets/CyberIcon.png";

const logos = {
  "/home": HomeIcon,
  "/physical": PhysicalIcon,
  "/mental": MentalIcon,
  "/vault": PasswordIcon,
  "/cyber": CyberIcon,
};

const Navbar = () => {
  const { pathname } = useLocation();
  const { logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
    document.body.style.overflow = !sidebarOpen ? "hidden" : "auto";
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
    document.body.style.overflow = "auto";
  };

  return (
    <>
      <nav className="navbar">
        <div className="navbar-logo">
          <img
            src={logos[pathname] || HomeIcon}
            alt="Logo"
            className="navbar-icon"
          />
          <Link to="/home" className="navbar-title">
            TrustGrid
          </Link>
        </div>

        {/* Desktop Links */}
        <div className="navbar-links">
          <Link to="/home">Home</Link>
          <Link to="/webappscanner">Webapp scanning</Link>
          <Link to="/domainscanner">Domain scanning</Link>
          <Link to="/networkscanner">Network scanning</Link>
          <Link to="/APIScanner">API scanning</Link>
          <Link to="/sslscanner">SSL/TLS</Link>
          <button className="logout-btn" onClick={logout}>
            Logout
          </button>
        </div>

        {/* Mobile Hamburger */}
        <div className="menu-icon" onClick={toggleSidebar}>
          <Menu size={28} color="#00f9ff" />
        </div>
      </nav>

      {/* Sidebar Drawer */}
      <div className={`sidebar-drawer ${sidebarOpen ? "open" : ""}`}>
        <button className="close-btn" onClick={closeSidebar}>
          ×
        </button>
        <div className="sidebar-content">
          <Link to="/home" onClick={closeSidebar}>
            Home
          </Link>
          <Link to="/webappscanner" onClick={closeSidebar}>
            Webapp scanning
          </Link>
          <Link to="/domainscanner" onClick={closeSidebar}>
            Domain scanning
          </Link>
          <Link to="/networkscanner" onClick={closeSidebar}>
            Network scanning
          </Link>
          <Link to="/APIScanner" onClick={closeSidebar}>
            API scanning
          </Link>
          <Link to="/sslscanner" onClick={closeSidebar}>
            SSL/TLS
          </Link>
          <button
            className="logout-btn"
            onClick={() => {
              closeSidebar();
              logout();
            }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Overlay */}
      {sidebarOpen && <div className="sidebar-overlay" onClick={closeSidebar}></div>}
    </>
  );
};

export default Navbar;

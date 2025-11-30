import React from "react";
import { Link } from "react-router-dom"; // Make sure to import Link
import "../styles/header.css";
import logo from "../assets/logo.png";
// Ensure this path is correct for the Icon component

const Header = ({
  activeLink = "Dashboard", // Default active link for highlighting
  storageUsedGB = 328,
  storageTotalGB = 1000,
}) => {
  const usagePercent = Math.round((storageUsedGB / storageTotalGB) * 100);

  // List of navigation items with paths
  const navItems = [
    { name: "Dashboard", path: "/dashboard" },
    { name: "Files", path: "/files" },
    { name: "Nodes", path: "/nodes" },
    { name: "Admin", path: "/admin" },
  ];

  return (
    <header className="compact-header-container">
      {/* --- Left Side: Logo and Navigation --- */}
      <div className="brand-section">
        <img src={logo} alt="CloudGrips Logo" className="brand-logo" />
        <span className="brand-name">CloudPlatform</span>

        <nav className="header-nav">
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.path}
              className={`nav-link ${activeLink === item.name ? "active" : ""}`}
            >
              {item.name}
            </Link>
          ))}
        </nav>
      </div>

      {/* --- Right Side: Storage and Profile --- */}
      <div className="right-actions">
        <div className="storage-indicator">
          <span className="storage-percentage">Storage {usagePercent}%</span>
          <div className="progress-bar-stack">
            <div className="progress-bar-container">
              <div
                className="progress-fill"
                style={{ width: `${usagePercent}%` }}
              ></div>
            </div>
            <span className="storage-usage-text">
              Used {storageUsedGB} GB of {storageTotalGB} GB
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

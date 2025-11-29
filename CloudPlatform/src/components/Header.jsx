import React from "react";
import "../styles/header.css";
import logo from "../assets/logo.png"; // Reusing your logo

// Placeholder for icons
const Icon = ({ name, className = "" }) => {
  const iconMap = {
    search: "🔍",
    bell: "🔔",
  };
  return <span className={`icon ${className}`}>{iconMap[name] || name}</span>;
};

const Header = ({ userName = "AD" }) => {
  return (
    <header className="app-header">
      {/* Brand Group */}
      <div className="header-brand-group">
        <img src={logo} alt="CloudVault Logo" className="header-logo" />
        <span className="header-brand-name">CloudVault</span>
      </div>

      {/* Global Search Bar */}
      <div className="header-search-bar">
        <Icon name="search" className="header-search-icon" />
        <input type="text" placeholder="Search files, users, and settings..." />
      </div>

      {/* Actions and Profile */}
      <div className="header-actions">
        {/* Notifications */}
        <div className="action-icon-wrapper">
          <Icon name="bell" className="action-icon" />
          <span className="notification-dot"></span>
        </div>

        {/* User Profile */}
        <div className="user-avatar">{userName}</div>
      </div>
    </header>
  );
};

export default Header;

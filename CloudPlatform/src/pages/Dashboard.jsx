import React from "react";
import "../styles/dashboard.css";
import logo from "../assets/logo.png"; // Make sure you have your logo here

// Placeholder for icons. In a real app, you'd use a library like 'react-icons'
const Icon = ({ name, className = "" }) => {
  // Simple mapping for visual representation, replace with actual icons
  const iconMap = {
    folder: "📁",
    file: "📄",
    document: "📄",
    pdf: " পিডিএফ", // Using a unicode char for PDF like icon
    image: "🖼️",
    search: "🔍",
    upload: "⬆️",
    bell: "🔔",
    settings: "⚙️",
    profile: "👤",
    shared: "👥",
    recent: "🕒",
    nodes: "🌐",
    trash: "🗑️",
    grid: "▦",
    list: "☰",
    "file-generic": "🗎", // Fallback for files
    chart: "📊", // For storage usage
  };
  return <span className={`icon ${className}`}>{iconMap[name] || name}</span>;
};

const Dashboard = () => {
  const files = [
    {
      id: 1,
      name: "Marketing Plan",
      size: "",
      type: "Folder",
      modified: "2 days ago",
      shared: true,
      iconType: "folder",
    },
    {
      id: 2,
      name: "Roadmap.docx",
      size: "1.2 MB",
      type: "Document",
      modified: "4 days ago",
      shared: false,
      iconType: "document",
    },
    {
      id: 3,
      name: "Presentation.pdf",
      size: "5.8 MB",
      type: "PDF",
      modified: "1 week ago",
      shared: false,
      iconType: "pdf",
    },
    {
      id: 4,
      name: "Header_Image.png",
      size: "3.4 MB",
      type: "Image",
      modified: "2 weeks ago",
      shared: true,
      iconType: "image",
    },
  ];

  return (
    <div className="dashboard-layout">
      {/* --- Sidebar --- */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <img src={logo} alt="CloudVault Logo" className="sidebar-logo" />
          <div>
            <div className="sidebar-brand-name">CloudVault</div>
            <div className="sidebar-brand-subtitle">Distributed Storage</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-item active">
            <Icon name="file" className="nav-icon" />
            <span>My Files</span>
          </div>
          <div className="nav-item">
            <Icon name="shared" className="nav-icon" />
            <span>Shared with Me</span>
          </div>
          <div className="nav-item">
            <Icon name="recent" className="nav-icon" />
            <span>Recent</span>
          </div>
          <div className="nav-item">
            <Icon name="nodes" className="nav-icon" />
            <span>Storage Nodes</span>
          </div>
          <div className="nav-item">
            <Icon name="trash" className="nav-icon" />
            <span>Trash</span>
          </div>
        </nav>

        <div className="storage-info">
          <div className="storage-title">Storage Used</div>
          <div className="progress-bar-container">
            <div className="progress-bar" style={{ width: "65%" }}></div>{" "}
            {/* Dynamic width */}
          </div>
          <div className="storage-text">65GB of 100GB used</div>
          <button className="upgrade-btn">Upgrade Plan</button>
        </div>

        <div className="sidebar-footer">
          <div className="nav-item">
            <Icon name="settings" className="nav-icon" />
            <span>Settings</span>
          </div>
          <div className="nav-item">
            <Icon name="profile" className="nav-icon" />
            <span>Profile</span>
          </div>
        </div>
      </aside>

      {/* --- Header --- */}
      <header className="header">
        <div className="search-bar">
          <Icon name="search" className="search-icon" />
          <input type="text" placeholder="Search files and folders..." />
        </div>
        <div className="header-actions">
          <button className="upload-btn">
            <Icon name="upload" />
            Upload
          </button>
          <div className="action-icon-wrapper">
            <Icon name="bell" className="action-icon" />
            <span className="notification-dot"></span>
          </div>
          <div className="user-avatar">AD</div>{" "}
          {/* Placeholder for user initials */}
        </div>
      </header>

      {/* --- Main Content --- */}
      <main className="main-content">
        <div className="breadcrumb">
          <a href="#myfiles">My Files</a> &gt; <a href="#projects">Projects</a>{" "}
          &gt; <span>Design</span>
        </div>

        <div className="content-header">
          <h1 className="page-title">My Files</h1>
          <div className="view-toggle">
            <button className="view-toggle-btn">
              <Icon name="grid" className="icon" />
            </button>
            <button className="view-toggle-btn active">
              <Icon name="list" className="icon" />
            </button>
          </div>
        </div>

        <table className="file-list">
          <thead>
            <tr>
              <th>Name</th>
              <th>Size</th>
              <th>Type</th>
              <th>Modified</th>
              <th>Shared</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file) => (
              <tr key={file.id}>
                <td className="file-name-cell">
                  <Icon
                    name={file.iconType}
                    className={`file-icon ${file.iconType}`}
                  />
                  {file.name}
                </td>
                <td>{file.size}</td>
                <td>{file.type}</td>
                <td>{file.modified}</td>
                <td>
                  {file.shared && (
                    <Icon name="shared" className="shared-icon" />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
    </div>
  );
};

export default Dashboard;

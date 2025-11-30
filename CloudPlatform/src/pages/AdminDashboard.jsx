import React from "react";
import "../styles/AdminDashboard.css";

// Placeholder for icons (only '+' for 'New Node' button is needed)
const Icon = ({ name, className = "" }) => {
  const iconMap = {
    add: "+",
  };
  return <span className={`icon ${className}`}>{iconMap[name] || name}</span>;
};

const KPICard = ({ metric, value, label }) => (
  <div className="kpi-card">
    <div className="kpi-metric">{value}</div>
    <div className="kpi-label">{label}</div>
  </div>
);

const StorageStatusCard = ({ label, percentage, description }) => (
  <div className="storage-status-card">
    <div className="storage-status-header">
      <span className="storage-status-label">{label}</span>
      <span className="storage-status-value">{percentage}%</span>
    </div>
    <div className="storage-progress-bar-container">
      <div
        className="storage-progress-fill"
        style={{ width: `${percentage}%` }}
      ></div>
    </div>
    <p className="storage-status-info">{description}</p>
  </div>
);

const AdminDashboard = () => {
  const kpiData = [
    { label: "Total Users", value: "1,423" },
    { label: "Total Files", value: "10,504" },
    { label: "Global Capacity (GB)", value: "8,192" },
    { label: "Online Nodes", value: "31" },
  ];

  // Data for the Storage Status cards
  const storageData = [
    {
      label: "Allocation %",
      percentage: 85,
      description: "Percentage of total capacity that has been allocated.",
    },
    {
      label: "Usage %",
      percentage: 62,
      description: "Percentage of allocated capacity that is actively in use.",
    },
  ];

  return (
    <div className="admin-overview-page">
      {/* --- Header & New Node Button --- */}
      <div className="overview-header">
        <h1 className="overview-title">Admin Dashboard</h1>
        <button className="new-node-btn">
          <Icon name="add" />
          New Node
        </button>
      </div>

      {/* --- Navigation Tabs --- */}
      <nav className="overview-tab-nav">
        <div className="tab-nav-item active">Overview</div>
        <div className="tab-nav-item">Nodes</div>
        <div className="tab-nav-item">Events</div>
      </nav>

      {/* --- System Overview KPIs --- */}
      <h2 className="section-title">System Overview</h2>
      <div className="kpi-grid">
        {kpiData.map((item, index) => (
          <KPICard key={index} label={item.label} value={item.value} />
        ))}
      </div>

      {/* --- Storage Status --- */}
      <h2 className="section-title">Storage Status</h2>
      <div className="storage-status-grid">
        {storageData.map((item, index) => (
          <StorageStatusCard
            key={index}
            label={item.label}
            percentage={item.percentage}
            description={item.description}
          />
        ))}
      </div>
    </div>
  );
};

export default AdminDashboard;

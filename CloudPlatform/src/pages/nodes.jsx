import React from "react";
import "../styles/node.css";

// Placeholder for icons
const Icon = ({ name, className = "" }) => {
  const iconMap = {
    add: "+",
    search: "🔍",
    grid: "▦",
    list: "☰",
  };
  return <span className={`icon ${className}`}>{iconMap[name] || name}</span>;
};

// Component for the Donut Chart (Simulated using CSS)
const DonutChart = ({
  percent,
  usedColor,
  allocatedColor,
  totalLabel,
  totalValue,
}) => {
  // In a real application, you'd use a charting library (e.g., Recharts, Chart.js)
  // The CSS here simulates the look.
  const usedPercentage = 75; // 750 TB / 1.0 PB (Allocated) * 100

  return (
    <div className="chart-section">
      {/* SVG placeholder for actual donut chart rendering */}
      <svg viewBox="0 0 100 100" width="100%" height="100%">
        {/* Background circle */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="#1f2937"
          strokeWidth="10"
        />
        {/* Used Storage Arc - simplified here, should use stroke-dasharray in real code */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={usedColor}
          strokeWidth="10"
          strokeDasharray={`${
            usedPercentage * 2.827
          } ${282.7}`} /* Circumference of r=45 is ~282.7 */
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="donut-chart-text">
        <div className="chart-value">{totalValue}</div>
        <div className="chart-label">{totalLabel}</div>
      </div>
    </div>
  );
};

// Component for an individual Node Status Card
const NodeCard = ({ node }) => {
  const statusClass = `status-${node.status.toLowerCase()}`;
  const barClass = `bar-${node.status.toLowerCase()}`;
  const healthBarColor =
    node.status === "Online"
      ? "#10b981"
      : node.status === "Warning"
      ? "#fbbf24"
      : "#ef4444";

  return (
    <div className="node-card">
      <div className="node-info">
        <div>
          <div className="node-id">{node.id}</div>
          <div className="node-ip">{node.ip}</div>
        </div>
        <span className={`node-status ${statusClass}`}>{node.status}</span>
      </div>

      <div className="capacity-title">
        Capacity: {node.used}/{node.total}
      </div>
      <div className="node-capacity-bar">
        <div
          className="bar-fill"
          style={{
            width: node.capacityPercent,
            backgroundColor: healthBarColor,
          }}
        ></div>
      </div>

      <div className="node-footer">
        <div>
          <div className="health-label">Health</div>
          <div className="health-value">{node.health}</div>
        </div>
        <div>
          <div className="last-seen-label">Last Seen</div>
          <div className="last-seen-value">{node.lastSeen}</div>
        </div>
      </div>
    </div>
  );
};

const NodesDashboard = () => {
  const nodes = [
    {
      id: "A4B1-C6D7-E3F2",
      ip: "192.168.1.101:9000",
      used: "18.6",
      total: "32.0 TB",
      capacityPercent: "58%",
      health: "99.8%",
      lastSeen: "2 min ago",
      status: "Online",
    },
    {
      id: "F9G5-H2I3-J4K1",
      ip: "192.168.1.102:9000",
      used: "26.1",
      total: "32.0 TB",
      capacityPercent: "82%",
      health: "0%",
      lastSeen: "3 hours ago",
      status: "Offline",
    },
    {
      id: "L6M8-N7P9-Q1R9",
      ip: "192.168.1.103:9000",
      used: "30.5",
      total: "32.0 TB",
      capacityPercent: "95%",
      health: "86.2%",
      lastSeen: "5 min ago",
      status: "Warning",
    },
  ];

  return (
    <div className="nodes-page">
      <div className="page-header">
        <div className="page-title-group">
          <h1>Storage & Nodes</h1>
          <p>
            Monitor the health and capacity of the CloudVault distributed
            storage network.
          </p>
        </div>
        <button className="add-node-btn">
          <Icon name="add" />
          Add Node
        </button>
      </div>

      {/* --- Top Dashboard Cards --- */}
      <div className="top-cards-container">
        {/* Global Storage Overview */}
        <div className="data-card">
          <h2 className="card-title">Global Storage Overview</h2>
          <div className="overview-content">
            <DonutChart
              percent={75}
              usedColor="#06b6d4"
              allocatedColor="#2563eb"
              totalLabel="Total Capacity"
              totalValue="1.2 PB"
            />
            <div className="legend">
              <div className="legend-item">
                <span className="legend-dot dot-used"></span>
                <span className="legend-text">Used Storage</span>
                <span className="legend-value">750 TB</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot dot-allocated"></span>
                <span className="legend-text">Allocated Storage</span>
                <span className="legend-value">1.0 PB</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot dot-free"></span>
                <span className="legend-text">Free</span>
                <span className="legend-value">200 TB</span>
              </div>
            </div>
          </div>
        </div>

        {/* Storage Growth Card */}
        <div className="data-card">
          <h2 className="card-title">Storage Growth (Last 24h)</h2>
          <div className="growth-header">
            <div className="growth-value">750 TB</div>
            <div className="growth-change">+5.2%</div>
          </div>
          <div className="growth-subtitle">Last 24 hours</div>

          <div className="chart-placeholder">
            [Placeholder for Line Chart: Storage Usage over 24h]
          </div>
        </div>
      </div>

      {/* --- Network Nodes Section --- */}
      <div className="nodes-section">
        <h2 className="card-title">Network Nodes</h2>
        <div className="nodes-section-header">
          <div className="nodes-search">
            <Icon name="search" className="search-icon" />
            <input
              type="text"
              placeholder="Search by Node ID, IP, or status..."
            />
          </div>
          <div className="view-toggle">
            <button className="view-toggle-btn active">
              <Icon name="grid" className="icon" />
            </button>
            <button className="view-toggle-btn">
              <Icon name="list" className="icon" />
            </button>
          </div>
        </div>

        <div className="nodes-grid">
          {nodes.map((node) => (
            <NodeCard key={node.id} node={node} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default NodesDashboard;

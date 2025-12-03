import { useState, useEffect } from "react";
import {
  Server,
  Plus,
  Play,
  Square,
  Trash2,
  RefreshCw,
  Wifi,
  WifiOff,
  HardDrive,
  AlertCircle,
  CheckCircle,
} from "lucide-react";

const AdminNodeManagerPage = () => {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newNode, setNewNode] = useState({
    node_id: "",
    host: "localhost",
    port: "",
    storage_gb: "",
  });
  const adminKey =
    typeof window !== "undefined" ? sessionStorage.getItem("adminKey") : null;

  useEffect(() => {
    loadNodes();
    const interval = setInterval(loadNodes, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadNodes = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/admin/nodes", {
        headers: {
          "X-Admin-Key": adminKey,
        },
      });
      const data = await response.json();
      if (data.success) {
        setNodes(data.data.nodes || []);
      }
    } catch (error) {
      console.error("Error loading nodes:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return "0 B";
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const getStatusColor = (status) => {
    return status === "online" ? "text-green-500" : "text-red-500";
  };

  const getStatusIcon = (status) => {
    return status === "online" ? (
      <Wifi className="w-5 h-5" />
    ) : (
      <WifiOff className="w-5 h-5" />
    );
  };

  const handleCreateNode = async () => {
    if (!newNode.node_id || !newNode.port || !newNode.storage_gb) {
      alert("Please fill in all fields");
      return;
    }

    try {
      const response = await fetch("/api/admin/nodes", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Key": adminKey,
        },
        body: JSON.stringify({
          node_id: newNode.node_id,
          host: newNode.host,
          port: parseInt(newNode.port),
          storage_gb: parseFloat(newNode.storage_gb),
        }),
      });

      const data = await response.json();
      if (data.success) {
        alert("Node created successfully! Click Start to launch it.");
        setShowCreateModal(false);
        setNewNode({
          node_id: "",
          host: "localhost",
          port: "",
          storage_gb: "",
        });
        loadNodes();
      } else {
        alert(data.message || "Failed to create node");
      }
    } catch (error) {
      alert("Failed to create node");
      console.error("Error creating node:", error);
    }
  };

  const handleStartNode = async (nodeId) => {
    try {
      const node = nodes.find((n) => n.node_id === nodeId);
      if (!node) return;

      const response = await fetch(`/api/admin/nodes/${nodeId}/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Key": adminKey,
        },
        body: JSON.stringify({
          host: node.host,
          port: node.port,
          storage_gb: node.storage_capacity / 1024 ** 3,
        }),
      });

      const data = await response.json();
      if (data.success) {
        alert(`Node ${nodeId} started successfully!`);
        setTimeout(loadNodes, 2000);
      } else {
        alert(data.message || "Failed to start node");
      }
    } catch (error) {
      alert("Failed to start node");
      console.error("Error starting node:", error);
    }
  };

  const handleStopNode = async (nodeId) => {
    if (!confirm(`Are you sure you want to stop node ${nodeId}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/admin/nodes/${nodeId}/stop`, {
        method: "POST",
        headers: {
          "X-Admin-Key": adminKey,
        },
      });

      const data = await response.json();
      if (data.success) {
        alert(`Node ${nodeId} stopped successfully`);
        loadNodes();
      } else {
        alert(data.message || "Failed to stop node");
      }
    } catch (error) {
      alert("Failed to stop node");
      console.error("Error stopping node:", error);
    }
  };

  const handleDeleteNode = async (nodeId) => {
    if (
      !confirm(
        `Are you sure you want to delete node ${nodeId}? This will:\n` +
          `- Stop the node if running\n` +
          `- Delete all stored chunks\n` +
          `- Remove node configuration\n\n` +
          `This action cannot be undone!`
      )
    ) {
      return;
    }

    try {
      const response = await fetch(`/api/admin/nodes/${nodeId}`, {
        method: "DELETE",
        headers: {
          "X-Admin-Key": adminKey,
        },
      });

      const data = await response.json();
      if (data.success) {
        alert(`Node ${nodeId} deleted successfully`);
        loadNodes();
      } else {
        alert(data.message || "Failed to delete node");
      }
    } catch (error) {
      alert("Failed to delete node");
      console.error("Error deleting node:", error);
    }
  };

  if (loading && nodes.length === 0) {
    return (
      <div className="p-6">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-6 animate-pulse"></div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-32 bg-gray-200 rounded animate-pulse"
            ></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-2">Storage Node Management</h1>
          <p className="text-gray-600">
            Full control over all storage nodes in the system
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={loadNodes}
            className="flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Node
          </button>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start space-x-3">
        <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-900">
          <p className="font-medium mb-1">Full Node Control Enabled</p>
          <p>
            You can now start, stop, and delete any node in the system,
            regardless of how it was created. Nodes auto-refresh every 5
            seconds. Online nodes send heartbeats every 30 seconds.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Total Nodes</span>
            <Server className="w-4 h-4 text-gray-600" />
          </div>
          <p className="text-2xl font-bold">{nodes.length}</p>
        </div>
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Online</span>
            <CheckCircle className="w-4 h-4 text-green-500" />
          </div>
          <p className="text-2xl font-bold text-green-500">
            {nodes.filter((n) => n.status === "online").length}
          </p>
        </div>
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Offline</span>
            <AlertCircle className="w-4 h-4 text-red-500" />
          </div>
          <p className="text-2xl font-bold text-red-500">
            {nodes.filter((n) => n.status === "offline").length}
          </p>
        </div>
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Total Capacity</span>
            <HardDrive className="w-4 h-4 text-gray-600" />
          </div>
          <p className="text-2xl font-bold">
            {formatBytes(nodes.reduce((sum, n) => sum + n.storage_capacity, 0))}
          </p>
        </div>
      </div>

      <div className="bg-white border rounded-lg">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold">Storage Nodes</h2>
        </div>
        <div className="divide-y">
          {nodes.length === 0 ? (
            <div className="p-12 text-center text-gray-600">
              <Server className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg mb-2">No storage nodes yet</p>
              <p className="text-sm">Create your first node to get started</p>
            </div>
          ) : (
            nodes.map((node) => (
              <div
                key={node.node_id}
                className="p-6 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    <div className={`mt-1 ${getStatusColor(node.status)}`}>
                      {getStatusIcon(node.status)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="font-semibold text-lg">
                          {node.node_id}
                        </h3>
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            node.status === "online"
                              ? "bg-green-100 text-green-700"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          {node.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-3">
                        {node.host}:{node.port}
                      </p>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Storage</span>
                          <span className="font-medium">
                            {formatBytes(node.storage_used)} /{" "}
                            {formatBytes(node.storage_capacity)}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                            style={{
                              width: `${
                                node.storage_capacity > 0
                                  ? (node.storage_used /
                                      node.storage_capacity) *
                                    100
                                  : 0
                              }%`,
                            }}
                          />
                        </div>
                        <div className="flex items-center justify-between text-xs text-gray-600">
                          <span>{node.chunk_count} chunks</span>
                          <span>Health: {node.health_score.toFixed(0)}%</span>
                        </div>
                        {node.last_heartbeat && (
                          <p className="text-xs text-gray-600">
                            Last seen:{" "}
                            {new Date(node.last_heartbeat).toLocaleString()}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    {node.status === "offline" ? (
                      <button
                        onClick={() => handleStartNode(node.node_id)}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                        title="Start Node"
                      >
                        <Play className="w-5 h-5" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStopNode(node.node_id)}
                        className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors"
                        title="Stop Node"
                      >
                        <Square className="w-5 h-5" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteNode(node.node_id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete Node"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white border rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create New Storage Node</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Node ID
                </label>
                <input
                  type="text"
                  value={newNode.node_id}
                  onChange={(e) =>
                    setNewNode({ ...newNode, node_id: e.target.value })
                  }
                  placeholder="e.g., node1"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Host</label>
                <input
                  type="text"
                  value={newNode.host}
                  onChange={(e) =>
                    setNewNode({ ...newNode, host: e.target.value })
                  }
                  placeholder="localhost"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Port</label>
                <input
                  type="number"
                  value={newNode.port}
                  onChange={(e) =>
                    setNewNode({ ...newNode, port: e.target.value })
                  }
                  placeholder="e.g., 9001"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Storage (GB)
                </label>
                <input
                  type="number"
                  value={newNode.storage_gb}
                  onChange={(e) =>
                    setNewNode({ ...newNode, storage_gb: e.target.value })
                  }
                  placeholder="e.g., 2"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateNode}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create Node
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminNodeManagerPage;

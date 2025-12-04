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
  Database,
  Activity,
} from "lucide-react";

const AdminNodeManagerPage = () => {
  const [nodes, setNodes] = useState([]);
  const [capacityMetrics, setCapacityMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [operatingNodes, setOperatingNodes] = useState(new Set());
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
        setCapacityMetrics(data.data.capacity_metrics || null);
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
      alert("Failed to create node: " + error.message);
      console.error("Error creating node:", error);
    }
  };

  const handleStartNode = async (nodeId) => {
    setOperatingNodes((prev) => new Set(prev).add(nodeId));

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
        alert(
          `Node ${nodeId} started successfully! It may take a few seconds to come online.`
        );
        await loadNodes();
        setTimeout(() => loadNodes(), 3000);
        setTimeout(() => loadNodes(), 6000);
      } else {
        alert(data.message || "Failed to start node");
      }
    } catch (error) {
      alert("Failed to start node: " + error.message);
      console.error("Error starting node:", error);
    } finally {
      setOperatingNodes((prev) => {
        const next = new Set(prev);
        next.delete(nodeId);
        return next;
      });
    }
  };

  const handleStopNode = async (nodeId) => {
    if (!confirm(`Are you sure you want to stop node ${nodeId}?`)) {
      return;
    }

    setOperatingNodes((prev) => new Set(prev).add(nodeId));

    try {
      const response = await fetch(`/api/admin/nodes/${nodeId}/stop`, {
        method: "POST",
        headers: {
          "X-Admin-Key": adminKey,
        },
      });

      const data = await response.json();
      if (data.success) {
        alert(
          `Node ${nodeId} stopped successfully. Usable capacity has been reduced.`
        );
        await loadNodes();
        setTimeout(loadNodes, 2000);
      } else {
        alert(data.message || "Failed to stop node");
      }
    } catch (error) {
      alert("Failed to stop node: " + error.message);
      console.error("Error stopping node:", error);
    } finally {
      setOperatingNodes((prev) => {
        const next = new Set(prev);
        next.delete(nodeId);
        return next;
      });
    }
  };

  const initiateDeleteNode = (nodeId) => {
    const node = nodes.find((n) => n.node_id === nodeId);
    setDeleteTarget({ nodeId, chunkCount: node?.chunk_count || 0 });
    setShowDeleteModal(true);
  };

  const handleDeleteNode = async (force = false) => {
    if (!deleteTarget) return;

    const { nodeId, chunkCount } = deleteTarget;

    try {
      const url = `/api/admin/nodes/${nodeId}${force ? "?force=true" : ""}`;
      const response = await fetch(url, {
        method: "DELETE",
        headers: {
          "X-Admin-Key": adminKey,
        },
      });

      const data = await response.json();

      if (data.success) {
        alert(
          `Node ${nodeId} deleted successfully! Total capacity has been reduced.`
        );
        setShowDeleteModal(false);
        setDeleteTarget(null);
        loadNodes();
      } else {
        // Show error with option to force delete
        if (data.message && data.message.includes("contains") && !force) {
          const forceConfirm = confirm(
            `${data.message}\n\n⚠️  WARNING: Force deleting will cause DATA LOSS!\n\nContinue anyway?`
          );
          if (forceConfirm) {
            handleDeleteNode(true); // Retry with force
          }
        } else {
          alert(data.message || "Failed to delete node");
        }
      }
    } catch (error) {
      alert("Failed to delete node: " + error.message);
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
          <p className="font-medium mb-1">Advanced Capacity Tracking</p>
          <p>
            <strong>Total Capacity</strong> = All nodes (reduces only when
            deleted) |<strong> Usable Capacity</strong> = Online nodes only
            (reduces when offline/paused)
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
            {capacityMetrics?.online_nodes || 0}
          </p>
        </div>

        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Offline</span>
            <AlertCircle className="w-4 h-4 text-red-500" />
          </div>
          <p className="text-2xl font-bold text-red-500">
            {capacityMetrics?.offline_nodes || 0}
          </p>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-blue-900 font-medium">
              Total Capacity
            </span>
            <Database className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-blue-900">
            {formatBytes(capacityMetrics?.total_capacity || 0)}
          </p>
          <p className="text-xs text-blue-700 mt-1">
            All nodes (incl. offline)
          </p>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-green-900 font-medium">
              Usable Capacity
            </span>
            <Activity className="w-4 h-4 text-green-600" />
          </div>
          <p className="text-2xl font-bold text-green-900">
            {formatBytes(capacityMetrics?.usable_capacity || 0)}
          </p>
          <p className="text-xs text-green-700 mt-1">Online nodes only</p>
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
                        {node.chunk_count > 0 && (
                          <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-700">
                            {node.chunk_count} chunks
                          </span>
                        )}
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
                        disabled={operatingNodes.has(node.node_id)}
                        className={`p-2 rounded-lg transition-colors ${
                          operatingNodes.has(node.node_id)
                            ? "text-gray-400 bg-gray-100 cursor-not-allowed"
                            : "text-green-600 hover:bg-green-50"
                        }`}
                        title="Start Node"
                      >
                        {operatingNodes.has(node.node_id) ? (
                          <RefreshCw className="w-5 h-5 animate-spin" />
                        ) : (
                          <Play className="w-5 h-5" />
                        )}
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStopNode(node.node_id)}
                        disabled={operatingNodes.has(node.node_id)}
                        className={`p-2 rounded-lg transition-colors ${
                          operatingNodes.has(node.node_id)
                            ? "text-gray-400 bg-gray-100 cursor-not-allowed"
                            : "text-yellow-600 hover:bg-yellow-50"
                        }`}
                        title="Stop Node"
                      >
                        {operatingNodes.has(node.node_id) ? (
                          <RefreshCw className="w-5 h-5 animate-spin" />
                        ) : (
                          <Square className="w-5 h-5" />
                        )}
                      </button>
                    )}
                    <button
                      onClick={() => initiateDeleteNode(node.node_id)}
                      disabled={operatingNodes.has(node.node_id)}
                      className={`p-2 rounded-lg transition-colors ${
                        operatingNodes.has(node.node_id)
                          ? "text-gray-400 bg-gray-100 cursor-not-allowed"
                          : "text-red-600 hover:bg-red-50"
                      }`}
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

      {/* Create Node Modal */}
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

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deleteTarget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white border rounded-lg p-6 w-full max-w-md">
            <div className="flex items-start space-x-3 mb-4">
              <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
              <div>
                <h2 className="text-xl font-bold text-red-900 mb-2">
                  Delete Node {deleteTarget.nodeId}?
                </h2>
                <div className="text-sm text-gray-700 space-y-2">
                  <p>This will permanently:</p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>Stop the node process if running</li>
                    <li>Remove node from database</li>
                    <li>Delete storage directory</li>
                    <li>Reduce total capacity</li>
                    {deleteTarget.chunkCount > 0 && (
                      <li className="text-red-600 font-medium">
                        Delete {deleteTarget.chunkCount} chunks (DATA LOSS!)
                      </li>
                    )}
                  </ul>
                  {deleteTarget.chunkCount > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded p-3 mt-3">
                      <p className="font-medium text-red-900">⚠️ Warning:</p>
                      <p className="text-red-800">
                        This node contains {deleteTarget.chunkCount} chunks.
                        Deleting will cause permanent data loss!
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteTarget(null);
                }}
                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteNode(false)}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                {deleteTarget.chunkCount > 0 ? "Force Delete" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminNodeManagerPage;

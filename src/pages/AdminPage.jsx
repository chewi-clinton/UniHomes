import React, { useState, useEffect, useRef } from "react";
import { adminAPI } from "../services/api";
import { toast } from "sonner";
import {
  Server,
  Users,
  HardDrive,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  User,
  Database,
  Wifi,
  WifiOff,
  RefreshCw,
  LogOut,
} from "lucide-react";

const AdminPage = () => {
  const [status, setStatus] = useState(null);
  const [users, setUsers] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const eventSourceRef = useRef(null);
  const adminKey = sessionStorage.getItem("adminKey");

  useEffect(() => {
    if (adminKey) {
      loadAdminData();
      connectToEvents();
    } else {
      window.location.href = "/admin/auth";
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const loadAdminData = async () => {
    try {
      setLoading(true);

      // Load system status
      const statusResponse = await adminAPI.getStatus(adminKey);
      if (statusResponse.data.success) {
        setStatus(statusResponse.data.data);
      }

      // Load users
      const usersResponse = await adminAPI.getUsers(adminKey);
      if (usersResponse.data.success) {
        setUsers(usersResponse.data.data.users || []);
      }

      // Load nodes
      const nodesResponse = await adminAPI.getNodes(adminKey);
      if (nodesResponse.data.success) {
        setNodes(nodesResponse.data.data.nodes || []);
      }
    } catch (error) {
      toast.error("Failed to load admin data");
      console.error("Error loading admin data:", error);
    } finally {
      setLoading(false);
    }
  };

  const connectToEvents = () => {
    try {
      eventSourceRef.current = adminAPI.getEvents(adminKey);

      eventSourceRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setEvents((prev) => [data, ...prev].slice(0, 50)); // Keep last 50 events
      };

      eventSourceRef.current.onerror = (error) => {
        console.error("SSE error:", error);
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            connectToEvents();
          }
        }, 5000);
      };
    } catch (error) {
      console.error("Failed to connect to events:", error);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem("adminKey");
    window.location.href = "/admin/auth";
  };

  const formatBytes = (bytes) => {
    if (!bytes) return "0 B";
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const getStatusColor = (health) => {
    if (health >= 80) return "text-green-500";
    if (health >= 50) return "text-yellow-500";
    return "text-red-500";
  };

  const getStatusIcon = (health) => {
    if (health >= 80) return <CheckCircle className="w-5 h-5" />;
    if (health >= 50) return <AlertCircle className="w-5 h-5" />;
    return <XCircle className="w-5 h-5" />;
  };

  const formatEventTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getEventIcon = (type) => {
    const iconMap = {
      USER_ENROLLED: <User className="w-4 h-4" />,
      USER_LOGIN: <User className="w-4 h-4" />,
      FILE_UPLOADED: <Database className="w-4 h-4" />,
      FILE_DOWNLOADED: <Database className="w-4 h-4" />,
      FILE_DELETED: <Database className="w-4 h-4" />,
      NODE_REGISTERED: <Server className="w-4 h-4" />,
      OTP_SENT: <AlertCircle className="w-4 h-4" />,
      OTP_VERIFIED: <CheckCircle className="w-4 h-4" />,
    };
    return iconMap[type] || <Activity className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="h-8 bg-muted rounded w-1/4 mb-6 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="h-32 bg-muted rounded animate-pulse"></div>
          <div className="h-32 bg-muted rounded animate-pulse"></div>
          <div className="h-32 bg-muted rounded animate-pulse"></div>
          <div className="h-32 bg-muted rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-2">Admin Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor system status, users, and real-time events
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={loadAdminData}
            className="flex items-center px-4 py-2 bg-accent hover:bg-accent/80 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={handleLogout}
            className="flex items-center px-4 py-2 bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </button>
        </div>
      </div>

      {/* System Status Cards */}
      {status && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium">Total Users</h3>
              <Users className="w-5 h-5 text-muted-foreground" />
            </div>
            <p className="text-3xl font-bold">{status.total_users || 0}</p>
            <p className="text-sm text-muted-foreground mt-1">
              Registered accounts
            </p>
          </div>

          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium">Storage Nodes</h3>
              <Server className="w-5 h-5 text-muted-foreground" />
            </div>
            <p className="text-3xl font-bold">
              {status.online_nodes || 0}/{status.total_nodes || 0}
            </p>
            <p className="text-sm text-muted-foreground mt-1">Nodes online</p>
          </div>

          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium">Total Files</h3>
              <Database className="w-5 h-5 text-muted-foreground" />
            </div>
            <p className="text-3xl font-bold">{status.total_files || 0}</p>
            <p className="text-sm text-muted-foreground mt-1">Files stored</p>
          </div>

          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium">System Health</h3>
              <Activity className="w-5 h-5 text-muted-foreground" />
            </div>
            <div className="flex items-center space-x-2">
              <div className={getStatusColor(status.system_health || 100)}>
                {getStatusIcon(status.system_health || 100)}
              </div>
              <span className="text-3xl font-bold">
                {status.system_health?.toFixed(0) || 100}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Storage Overview */}
      {status && (
        <div className="bg-card border rounded-lg p-6">
          <h3 className="font-medium mb-4">Storage Overview</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">Total Capacity</span>
                <span className="font-medium">
                  {formatBytes(status.global_capacity_bytes)}
                </span>
              </div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">Allocated</span>
                <span className="font-medium">
                  {formatBytes(status.global_allocated_bytes)}
                </span>
              </div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">Used</span>
                <span className="font-medium">
                  {formatBytes(status.global_used_bytes)}
                </span>
              </div>
              <div className="w-full bg-accent rounded-full h-3 mt-4">
                <div
                  className="bg-primary h-3 rounded-full transition-all duration-500"
                  style={{
                    width: `${
                      status.global_capacity_bytes > 0
                        ? (status.global_used_bytes /
                            status.global_capacity_bytes) *
                          100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Nodes and Users */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Storage Nodes */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="font-medium mb-4">Storage Nodes</h3>
          <div className="space-y-3">
            {nodes.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <HardDrive className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No storage nodes registered</p>
              </div>
            ) : (
              nodes.map((node) => (
                <div
                  key={node.node_id}
                  className="flex items-center justify-between p-3 bg-accent rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className={
                        node.status === "online"
                          ? "text-green-500"
                          : "text-red-500"
                      }
                    >
                      {node.status === "online" ? (
                        <Wifi className="w-5 h-5" />
                      ) : (
                        <WifiOff className="w-5 h-5" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">{node.node_id}</p>
                      <p className="text-sm text-muted-foreground">
                        {node.host}:{node.port}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {formatBytes(node.storage_used)}/
                      {formatBytes(node.storage_capacity)}
                    </p>
                    <p className="text-xs text-muted-foreground capitalize">
                      {node.status}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="font-medium mb-4">Recent Users</h3>
          <div className="space-y-3">
            {users.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No users registered</p>
              </div>
            ) : (
              users.slice(0, 8).map((user) => (
                <div
                  key={user.user_id}
                  className="flex items-center justify-between p-3 bg-accent rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-medium text-sm">
                      {user.name
                        ? user.name.charAt(0).toUpperCase()
                        : user.email.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium">{user.name || user.email}</p>
                      <p className="text-sm text-muted-foreground">
                        {user.email}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {formatBytes(user.storage_used)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {user.file_count || 0} files
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Real-time Events */}
      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Real-time Events</h3>
          <Activity className="w-5 h-5 text-muted-foreground animate-pulse" />
        </div>

        <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
          {events.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Waiting for events...</p>
            </div>
          ) : (
            events.map((event, index) => (
              <div
                key={index}
                className="flex items-center space-x-3 p-3 bg-accent rounded-lg"
              >
                <div className="flex-shrink-0">
                  {getEventIcon(event.event_type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{event.message}</p>
                  <p className="text-xs text-muted-foreground">
                    {event.user_id && `${event.user_id} • `}
                    {formatEventTime(event.timestamp)}
                  </p>
                </div>
                <div className="text-xs text-muted-foreground">
                  {event.event_type}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminPage;

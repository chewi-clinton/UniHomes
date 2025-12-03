import React, { useState, useEffect } from "react";
import {
  Shield,
  Key,
  Loader2,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle,
} from "lucide-react";

// Admin API service
const adminAPI = {
  verifyAdminKey: async (adminKey) => {
    const response = await fetch("/api/admin/verify", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ admin_key: adminKey }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Verification failed");
    }

    return data;
  },

  getSystemStatus: async (adminKey) => {
    const response = await fetch("/api/admin/status", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Key": adminKey,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to fetch system status");
    }

    return data;
  },

  getUsers: async (adminKey) => {
    const response = await fetch("/api/admin/users", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Key": adminKey,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to fetch users");
    }

    return data;
  },

  getNodes: async (adminKey) => {
    const response = await fetch("/api/admin/nodes", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Key": adminKey,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to fetch nodes");
    }

    return data;
  },
};

const AdminAuthPage = () => {
  const [adminKey, setAdminKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  // Check if admin is already authenticated on mount
  useEffect(() => {
    const storedAdminKey = sessionStorage.getItem("adminKey");
    if (storedAdminKey) {
      // Redirect immediately if already authenticated
      window.location.href = "/admin";
    }
  }, []);

  const verifyAndLoadDashboard = async (key, silent = false) => {
    try {
      setLoading(true);

      // Verify admin key with backend
      const verifyResult = await adminAPI.verifyAdminKey(key);

      if (verifyResult.success) {
        // Store admin key
        sessionStorage.setItem("adminKey", key);

        if (!silent) {
          setMessage({
            type: "success",
            text: "Admin access granted! Redirecting...",
          });
        }

        // Redirect to admin dashboard after short delay
        setTimeout(() => {
          window.location.href = "/admin";
        }, 1000);
      } else {
        if (!silent) {
          setMessage({
            type: "error",
            text: verifyResult.message || "Invalid admin key. Access denied.",
          });
        }
        sessionStorage.removeItem("adminKey");
        return false;
      }
    } catch (error) {
      console.error("Admin verification error:", error);
      if (!silent) {
        setMessage({
          type: "error",
          text:
            error.message || "Failed to verify admin key. Please try again.",
        });
      }
      sessionStorage.removeItem("adminKey");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!adminKey.trim()) {
      setMessage({ type: "error", text: "Please enter an admin key" });
      return;
    }

    setMessage({ type: "", text: "" });
    await verifyAndLoadDashboard(adminKey.trim());
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && adminKey.trim() && !loading) {
      handleSubmit(e);
    }
  };

  // Login Form View
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Shield className="w-12 h-12 text-white mr-3" />
            <h1 className="text-3xl font-bold text-white">Admin Access</h1>
          </div>
          <p className="text-white/80">Secure administrative portal</p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Key className="w-8 h-8 text-purple-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Authentication Required
              </h2>
              <p className="text-gray-600">
                Enter your admin key to access the dashboard
              </p>
            </div>

            <div className="space-y-4">
              <div className="relative">
                <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showKey ? "text" : "password"}
                  placeholder="Enter admin key"
                  value={adminKey}
                  onChange={(e) => setAdminKey(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={loading}
                  className="w-full pl-12 pr-12 py-3 bg-gray-50 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  disabled={loading}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
                >
                  {showKey ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>

              <button
                onClick={handleSubmit}
                disabled={loading || !adminKey.trim()}
                className="w-full bg-purple-600 text-white py-3 rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Shield className="w-5 h-5 mr-2" />
                    Access Admin Portal
                  </>
                )}
              </button>
            </div>

            {/* Messages */}
            {message.text && (
              <div
                className={`p-4 rounded-lg flex items-start ${
                  message.type === "error"
                    ? "bg-red-50 border border-red-200"
                    : "bg-green-50 border border-green-200"
                }`}
              >
                {message.type === "error" ? (
                  <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                )}
                <p
                  className={`text-sm ${
                    message.type === "error" ? "text-red-800" : "text-green-800"
                  }`}
                >
                  {message.text}
                </p>
              </div>
            )}

            {/* Security Notice */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-600 text-center">
                🔒 This is a secure area. All access attempts are logged.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-white/60 text-sm">
            Not an admin?{" "}
            <a
              href="/login"
              className="text-white hover:text-white/80 font-medium transition-colors underline"
            >
              Go to user login
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminAuthPage;

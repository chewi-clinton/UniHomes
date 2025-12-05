// src/pages/AdminAuthPage.jsx
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
import logo from "../img/logo.png"; // Your FileSphere logo

// Admin API service (unchanged)
const adminAPI = {
  verifyAdminKey: async (adminKey) => {
    const response = await fetch("/api/admin/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ admin_key: adminKey }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Verification failed");
    return data;
  },
};

const AdminAuthPage = () => {
  const [adminKey, setAdminKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    if (sessionStorage.getItem("adminKey")) {
      window.location.href = "/admin";
    }
  }, []);

  const verifyAndLoadDashboard = async (key) => {
    try {
      setLoading(true);
      const result = await adminAPI.verifyAdminKey(key);
      if (result.success) {
        sessionStorage.setItem("adminKey", key);
        setMessage({ type: "success", text: "Access granted! Redirecting..." });
        setTimeout(() => {
          window.location.href = "/admin";
        }, 1200);
      }
    } catch (error) {
      setMessage({ type: "error", text: error.message || "Invalid admin key" });
      sessionStorage.removeItem("adminKey");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!adminKey.trim()) {
      setMessage({ type: "error", text: "Please enter your admin key" });
      return;
    }
    setMessage({ type: "", text: "" });
    verifyAndLoadDashboard(adminKey.trim());
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="w-full max-w-md">
        {/* Logo + Brand */}
        <div className="text-center mb-10">
          <div className="flex flex-col items-center">
            <img
              src={logo}
              alt="FileSphere"
              className="w-20 h-20 object-contain mb-4 rounded-xl shadow-2xl"
            />
            <h1 className="text-4xl font-bold text-white tracking-tight">
              FileSphere
            </h1>
            <p className="text-white/70 mt-2 text-lg">Admin Portal</p>
          </div>
        </div>

        {/* Auth Card */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Shield className="w-9 h-9 text-primary" />
            </div>
            <h2 className="text-2xl font-bold text-white">
              Secure Access Required
            </h2>
            <p className="text-white/70 mt-2">
              Enter your admin key to continue
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="relative">
              <Key className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/60" />
              <input
                type={showKey ? "text" : "password"}
                placeholder="Admin Key"
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                disabled={loading}
                className="w-full pl-12 pr-12 py-4 bg-white/10 border border-white/30 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all disabled:opacity-60"
                autoFocus
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-white/60 hover:text-white transition-colors"
              >
                {showKey ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>

            <button
              type="submit"
              disabled={loading || !adminKey.trim()}
              className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Shield className="w-5 h-5" />
                  <span>Enter Admin Portal</span>
                </>
              )}
            </button>
          </form>

          {/* Message */}
          {message.text && (
            <div
              className={`mt-6 p-4 rounded-xl border flex items-start space-x-3 ${
                message.type === "error"
                  ? "bg-red-500/10 border-red-500/50 text-red-300"
                  : "bg-green-500/10 border-green-500/50 text-green-300"
              }`}
            >
              {message.type === "error" ? (
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              ) : (
                <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              )}
              <p className="text-sm">{message.text}</p>
            </div>
          )}

          {/* Security Notice */}
          <div className="mt-8 text-center">
            <p className="text-white/50 text-xs">
              This area is restricted. All access attempts are logged and
              monitored.
            </p>
          </div>

          {/* User Login Link */}
          <div className="mt-8 text-center">
            <a
              href="/login"
              className="text-white/70 hover:text-white text-sm underline transition-colors"
            >
              ← Back to user login
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminAuthPage;

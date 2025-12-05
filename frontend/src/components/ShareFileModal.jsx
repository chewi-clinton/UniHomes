import React, { useState } from "react";
import { Share2, X, Check, AlertCircle, Mail, Shield } from "lucide-react";

const ShareFileModal = ({ file, onClose, onShare }) => {
  const [email, setEmail] = useState("");
  const [permission, setPermission] = useState("read");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleShare = async () => {
    if (!email || !email.includes("@")) {
      setError("Please enter a valid email address");
      return;
    }

    setError("");
    setLoading(true);

    try {
      await onShare(file.id, email, permission);
      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to share file");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-border rounded-xl shadow-2xl max-w-md w-full animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Share2 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Share File</h2>
              <p className="text-sm text-muted-foreground truncate max-w-xs">
                {file.name}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Success Message */}
        {success && (
          <div className="p-4 mx-6 mt-6 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center space-x-3">
            <Check className="w-5 h-5 text-green-500 flex-shrink-0" />
            <p className="text-sm text-green-500">File shared successfully!</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-4 mx-6 mt-6 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* Form */}
        <div className="p-6 space-y-4">
          {/* Email Input */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Share with email address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    handleShare();
                  }
                }}
                placeholder="user@example.com"
                disabled={loading || success}
                className="w-full pl-10 pr-4 py-2 bg-accent border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all disabled:opacity-50"
              />
            </div>
          </div>

          {/* Permission Select */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Permission level
            </label>
            <div className="relative">
              <Shield className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <select
                value={permission}
                onChange={(e) => setPermission(e.target.value)}
                disabled={loading || success}
                className="w-full pl-10 pr-4 py-2 bg-accent border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all appearance-none disabled:opacity-50 cursor-pointer"
              >
                <option value="read">View only</option>
                <option value="write">Can download</option>
              </select>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {permission === "read"
                ? "User can view file details but cannot download"
                : "User can view and download the file"}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-accent text-accent-foreground rounded-lg hover:bg-accent/80 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleShare}
              disabled={loading || success}
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground"></div>
                  <span>Sharing...</span>
                </>
              ) : success ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>Shared!</span>
                </>
              ) : (
                <>
                  <Share2 className="w-4 h-4" />
                  <span>Share File</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShareFileModal;

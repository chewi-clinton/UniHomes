import React, { useState, useEffect } from "react";
import { storageAPI } from "../services/api";
import { formatFileSize } from "../utils/helpers";

const StorageProgress = () => {
  const [storageInfo, setStorageInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStorageInfo();

    // Refresh storage info every 30 seconds
    const interval = setInterval(loadStorageInfo, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStorageInfo = async () => {
    try {
      const response = await storageAPI.getStorageInfo();

      if (response.data.success) {
        const data = response.data.data;

        // Handle different property name formats from backend
        const allocated = data.allocated_bytes || data.allocated || 0;
        const used = data.used_bytes || data.used || 0;

        setStorageInfo({
          allocated: allocated,
          used: used,
          available: allocated - used,
          percentage: allocated > 0 ? (used / allocated) * 100 : 0,
        });
      }
    } catch (error) {
      console.error("Failed to load storage info:", error);
      // Set default values on error
      setStorageInfo({
        allocated: 0,
        used: 0,
        available: 0,
        percentage: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-2">
        <div className="h-4 bg-muted rounded animate-pulse"></div>
        <div className="h-2 bg-muted rounded animate-pulse"></div>
      </div>
    );
  }

  if (!storageInfo) {
    return null;
  }

  const usagePercentage = Math.min(storageInfo.percentage, 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">Storage</span>
        <span className="font-medium">
          {formatFileSize(storageInfo.used)} /{" "}
          {formatFileSize(storageInfo.allocated)}
        </span>
      </div>

      <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            usagePercentage >= 90
              ? "bg-destructive"
              : usagePercentage >= 70
              ? "bg-yellow-500"
              : "bg-primary"
          }`}
          style={{ width: `${usagePercentage}%` }}
        />
      </div>

      <p className="text-xs text-muted-foreground">
        {usagePercentage.toFixed(1)}% used •{" "}
        {formatFileSize(storageInfo.available)} free
      </p>
    </div>
  );
};

export default StorageProgress;

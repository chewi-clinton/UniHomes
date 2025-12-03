import React, { useState, useEffect } from "react";
import { storageAPI, filesAPI } from "../services/api";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import {
  HardDrive,
  Folder,
  File,
  Image,
  Film,
  Music,
  Archive,
} from "lucide-react";
import { formatFileSize } from "../utils/helpers";
import { toast } from "sonner";

const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#6b7280",
];

const StoragePage = () => {
  const [storageInfo, setStorageInfo] = useState(null);
  const [fileStats, setFileStats] = useState([]);
  const [recentFiles, setRecentFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStorageData();
  }, []);

  const loadStorageData = async () => {
    try {
      setLoading(true);

      // Load storage info
      const storageResponse = await storageAPI.getStorageInfo();
      if (storageResponse.data.success) {
        const data = storageResponse.data.data;
        setStorageInfo({
          allocated: data.allocated_bytes || data.allocated || 0,
          used: data.used_bytes || data.used || 0,
          available: data.available_bytes || data.available || 0,
        });
      }

      // Load files for statistics
      const filesResponse = await filesAPI.listFiles();
      if (filesResponse.data.success) {
        const responseData = filesResponse.data.data;
        let files = [];

        if (Array.isArray(responseData)) {
          files = responseData;
        } else if (responseData.files && Array.isArray(responseData.files)) {
          files = responseData.files;
        }

        const normalizedFiles = files.map((file) => ({
          id: file.file_id || file.id,
          name: file.filename || file.name,
          size: file.file_size || file.size || 0,
          type: file.type || "file",
          created_at: file.created_at || file.uploaded_at,
        }));

        calculateFileStats(normalizedFiles);
        setRecentFiles(normalizedFiles.slice(0, 10));
      }
    } catch (error) {
      toast.error("Failed to load storage data");
      console.error("Error loading storage data:", error);
    } finally {
      setLoading(false);
    }
  };

  const calculateFileStats = (files) => {
    const stats = {
      images: { count: 0, size: 0, name: "Images" },
      videos: { count: 0, size: 0, name: "Videos" },
      documents: { count: 0, size: 0, name: "Documents" },
      audio: { count: 0, size: 0, name: "Audio" },
      archives: { count: 0, size: 0, name: "Archives" },
      others: { count: 0, size: 0, name: "Others" },
    };

    files.forEach((file) => {
      if (file.type === "folder" || !file.name) return;

      const extension = file.name.split(".").pop().toLowerCase();

      if (["jpg", "jpeg", "png", "gif", "svg", "webp"].includes(extension)) {
        stats.images.count++;
        stats.images.size += file.size;
      } else if (
        ["mp4", "avi", "mov", "wmv", "flv", "mkv"].includes(extension)
      ) {
        stats.videos.count++;
        stats.videos.size += file.size;
      } else if (
        ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt"].includes(
          extension
        )
      ) {
        stats.documents.count++;
        stats.documents.size += file.size;
      } else if (["mp3", "wav", "flac", "aac", "ogg"].includes(extension)) {
        stats.audio.count++;
        stats.audio.size += file.size;
      } else if (["zip", "rar", "7z", "tar", "gz"].includes(extension)) {
        stats.archives.count++;
        stats.archives.size += file.size;
      } else {
        stats.others.count++;
        stats.others.size += file.size;
      }
    });

    setFileStats(Object.values(stats).filter((stat) => stat.count > 0));
  };

  // Convert bytes to MB for better chart readability
  const convertToMB = (bytes) => {
    return (bytes / (1024 * 1024)).toFixed(2);
  };

  const pieChartData = storageInfo
    ? [
        { name: "Used", value: storageInfo.used },
        { name: "Free", value: storageInfo.allocated - storageInfo.used },
      ]
    : [];

  // Convert file stats to MB for the bar chart
  const fileStatsInMB = fileStats.map((stat) => ({
    name: stat.name,
    sizeMB: parseFloat(convertToMB(stat.size)),
    count: stat.count,
    sizeBytes: stat.size,
  }));

  const getFileTypeIcon = (type) => {
    switch (type) {
      case "Images":
        return <Image className="w-5 h-5" />;
      case "Videos":
        return <Film className="w-5 h-5" />;
      case "Documents":
        return <File className="w-5 h-5" />;
      case "Audio":
        return <Music className="w-5 h-5" />;
      case "Archives":
        return <Archive className="w-5 h-5" />;
      default:
        return <File className="w-5 h-5" />;
    }
  };

  // Custom tooltip for the bar chart
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-popover border rounded-lg p-3 shadow-lg">
          <p className="font-medium">{payload[0].payload.name}</p>
          <p className="text-sm text-muted-foreground">
            Size: {formatFileSize(payload[0].payload.sizeBytes)}
          </p>
          <p className="text-sm text-muted-foreground">
            Files: {payload[0].payload.count}
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="h-8 bg-muted rounded w-1/4 mb-6 animate-pulse"></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 bg-muted rounded animate-pulse"></div>
          <div className="h-64 bg-muted rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-2">Storage Overview</h1>
        <p className="text-muted-foreground">
          Monitor your storage usage and file distribution
        </p>
      </div>

      {/* Storage Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Total Storage</h3>
            <HardDrive className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold mb-1">
            {storageInfo ? formatFileSize(storageInfo.allocated) : "0 GB"}
          </p>
          <p className="text-sm text-muted-foreground">Total available space</p>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Used Storage</h3>
            <Folder className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold mb-1">
            {storageInfo ? formatFileSize(storageInfo.used) : "0 GB"}
          </p>
          <p className="text-sm text-muted-foreground">
            {storageInfo
              ? Math.round((storageInfo.used / storageInfo.allocated) * 100)
              : 0}
            % of total
          </p>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Free Storage</h3>
            <File className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold mb-1">
            {storageInfo
              ? formatFileSize(storageInfo.allocated - storageInfo.used)
              : "0 GB"}
          </p>
          <p className="text-sm text-muted-foreground">
            Available for new files
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Storage Usage Pie Chart */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="font-medium mb-4">Storage Usage</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatFileSize(value)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* File Types Bar Chart - Now in MB */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="font-medium mb-4">File Types (MB)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={fileStatsInMB}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis
                  label={{
                    value: "Size (MB)",
                    angle: -90,
                    position: "insideLeft",
                  }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="sizeMB" fill="#3b82f6" name="Size (MB)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* File Type Statistics */}
      <div className="bg-card border rounded-lg p-6">
        <h3 className="font-medium mb-4">File Type Breakdown</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {fileStats.map((stat, index) => (
            <div
              key={stat.name}
              className="flex items-center justify-between p-4 bg-accent rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-background rounded-lg">
                  {getFileTypeIcon(stat.name)}
                </div>
                <div>
                  <p className="font-medium">{stat.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {stat.count} files
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-medium">{formatFileSize(stat.size)}</p>
                <p className="text-sm text-muted-foreground">
                  {Math.round((stat.size / (storageInfo?.used || 1)) * 100)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Files */}
      <div className="bg-card border rounded-lg p-6">
        <h3 className="font-medium mb-4">Recent Files</h3>
        <div className="space-y-3">
          {recentFiles.length > 0 ? (
            recentFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center justify-between p-3 hover:bg-accent rounded-lg transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <File className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {file.type === "folder" ? "Folder" : "File"}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">
                    {formatFileSize(file.size)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(file.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No files found
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default StoragePage;

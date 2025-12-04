import React, { useState, useEffect } from "react";
import { filesAPI } from "../services/api";
import { toast } from "sonner";
import { Users, Download, Mail, Clock, AlertCircle } from "lucide-react";
import { formatFileSize, formatDate } from "../utils/helpers";
import { ListSkeleton } from "../components/LoadingSpinner";

const SharedFilesPage = () => {
  const [sharedFiles, setSharedFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    loadSharedFiles();
  }, []);

  const loadSharedFiles = async () => {
    try {
      setLoading(true);
      const response = await filesAPI.getSharedFiles();
      if (response.data.success) {
        setSharedFiles(response.data.data.shared_files || []);
      }
    } catch (error) {
      toast.error("Failed to load shared files");
      console.error("Error loading shared files:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (file) => {
    if (file.permission !== "write") {
      toast.error("You do not have download permission for this file");
      return;
    }

    try {
      setDownloading(file.file_id);
      const loadingToast = toast.loading(`Downloading ${file.filename}...`);

      const response = await filesAPI.downloadFile(file.file_id);

      // Create blob and download
      const blob = new Blob([response.data], {
        type: file.mime_type || "application/octet-stream",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = file.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.dismiss(loadingToast);
      toast.success(`${file.filename} downloaded successfully!`);
    } catch (error) {
      console.error("Download error:", error);
      toast.error(`Failed to download ${file.filename}`);
    } finally {
      setDownloading(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="h-8 bg-muted rounded w-1/4 mb-6 animate-pulse"></div>
        <ListSkeleton />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Users className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">Shared with Me</h1>
        </div>
        <p className="text-muted-foreground">
          Files that others have shared with you ({sharedFiles.length}{" "}
          {sharedFiles.length === 1 ? "file" : "files"})
        </p>
      </div>

      {/* Empty State */}
      {sharedFiles.length === 0 && (
        <div className="text-center py-12">
          <div className="w-24 h-24 mx-auto mb-4 bg-accent rounded-full flex items-center justify-center">
            <Users className="w-12 h-12 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium mb-2">No shared files yet</h3>
          <p className="text-muted-foreground">
            When someone shares a file with you, it will appear here
          </p>
        </div>
      )}

      {/* Shared Files List */}
      {sharedFiles.length > 0 && (
        <div className="space-y-3">
          {sharedFiles.map((file) => (
            <div
              key={file.file_id}
              className="bg-card border border-border rounded-lg p-5 hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0 mr-4">
                  {/* File Info */}
                  <div className="flex items-center space-x-3 mb-2 flex-wrap">
                    <h3 className="font-semibold text-lg truncate">
                      {file.filename}
                    </h3>
                    <span
                      className={`px-2 py-1 text-xs rounded-full whitespace-nowrap ${
                        file.permission === "write"
                          ? "bg-green-500/10 text-green-500"
                          : "bg-blue-500/10 text-blue-500"
                      }`}
                    >
                      {file.permission === "write"
                        ? "Can download"
                        : "View only"}
                    </span>
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center flex-wrap gap-x-4 gap-y-2 text-sm text-muted-foreground">
                    <div className="flex items-center space-x-1">
                      <Mail className="w-4 h-4 flex-shrink-0" />
                      <span>Shared by {file.shared_by_email}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4 flex-shrink-0" />
                      <span>{formatDate(file.shared_at)}</span>
                    </div>
                  </div>
                </div>

                {/* Download Button */}
                {file.permission === "write" ? (
                  <button
                    onClick={() => handleDownload(file)}
                    disabled={downloading === file.file_id}
                    className="flex items-center space-x-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 whitespace-nowrap"
                  >
                    {downloading === file.file_id ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground"></div>
                        <span>Downloading...</span>
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4" />
                        <span>Download</span>
                      </>
                    )}
                  </button>
                ) : (
                  <div className="flex items-center space-x-2 text-muted-foreground text-sm px-4 py-2">
                    <AlertCircle className="w-4 h-4" />
                    <span>View only</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SharedFilesPage;

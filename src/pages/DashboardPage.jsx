import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { filesAPI } from "../services/api";
import { toast } from "sonner";
import {
  Upload,
  FolderPlus,
  Grid,
  List,
  Download,
  Trash2,
  MoreVertical,
  File,
  Folder,
  Image,
  FileText,
  Video,
  Music,
  Archive,
  Search,
} from "lucide-react";
import { formatFileSize, formatDate, getFileType } from "../utils/helpers";
import { FileSkeleton, ListSkeleton } from "../components/LoadingSpinner";
import FileUpload from "../components/FileUpload";
import ContextMenu from "../components/ContextMenu";
import Breadcrumb from "../components/Breadcrumb";

const DashboardPage = () => {
  const { folderId } = useParams();
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState("grid");
  const [showUpload, setShowUpload] = useState(false);
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    loadFiles();
  }, [folderId]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const response = await filesAPI.listFiles(folderId);
      if (response.data.success) {
        const data = response.data.data;
        const allFiles = data.files || [];
        const allFolders = data.folders || [];

        const transformedFolders = allFolders.map((folder) => ({
          id: folder.folder_id,
          name: folder.folder_name,
          type: "folder",
          created_at: folder.created_at,
          file_count: folder.file_count,
        }));

        const transformedFiles = allFiles.map((file) => ({
          id: file.file_id,
          name: file.filename,
          type: "file",
          size: file.file_size,
          mime_type: file.mime_type,
          created_at: file.created_at,
          modified_at: file.modified_at,
          is_shared: file.is_shared,
        }));

        setFiles([...transformedFolders, ...transformedFiles]);
      }
    } catch (error) {
      toast.error("Failed to load files");
      console.error("Error loading files:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    try {
      const response = await filesAPI.uploadFile(file, folderId);
      if (response.data.success) {
        toast.success(`${file.name} uploaded successfully!`);
        loadFiles();
      }
    } catch (error) {
      toast.error(`Failed to upload ${file.name}`);
      console.error("Upload error:", error);
    }
  };

  const handleFolderCreate = async () => {
    const name = prompt("Enter folder name:");
    if (name && name.trim()) {
      try {
        const response = await filesAPI.createFolder(name.trim(), folderId);
        if (response.data.success) {
          toast.success("Folder created successfully!");
          loadFiles();
        }
      } catch (error) {
        toast.error("Failed to create folder");
      }
    }
  };

  const handleFileDelete = async (file) => {
    if (confirm(`Are you sure you want to delete "${file.name}"?`)) {
      try {
        const response = await filesAPI.deleteFile(file.id);
        if (response.data.success) {
          toast.success(`${file.name} deleted successfully!`);
          loadFiles();
        }
      } catch (error) {
        toast.error(`Failed to delete ${file.name}`);
      }
    }
  };

  const handleFileDownload = async (file) => {
    if (downloading) {
      console.log("[DOWNLOAD] Already downloading a file");
      return;
    }

    try {
      setDownloading(file.id);
      console.log(`[DOWNLOAD] Starting download for ${file.name} (${file.id})`);

      // Show loading toast
      const loadingToast = toast.loading(`Downloading ${file.name}...`);

      // Make the download request
      const response = await filesAPI.downloadFile(file.id);

      console.log(`[DOWNLOAD] Response received`);
      console.log(`[DOWNLOAD] Status:`, response.status);
      console.log(`[DOWNLOAD] Response type:`, response.data.type);
      console.log(`[DOWNLOAD] Response size:`, response.data.size, "bytes");

      // Check if we got an error response disguised as blob
      if (response.data.type === "application/json") {
        // This is likely an error response
        const text = await response.data.text();
        console.error("[DOWNLOAD ERROR] Received JSON error:", text);
        const errorData = JSON.parse(text);
        throw new Error(errorData.message || "Download failed");
      }

      // Verify we received blob data
      if (!response.data || !(response.data instanceof Blob)) {
        throw new Error("Invalid response: expected Blob data");
      }

      if (response.data.size === 0) {
        throw new Error(
          "Received empty file - file may not have been uploaded correctly"
        );
      }

      // Create blob with correct mime type
      const blob = new Blob([response.data], {
        type:
          file.mime_type || response.data.type || "application/octet-stream",
      });

      console.log(`[DOWNLOAD] Blob created, size: ${blob.size} bytes`);

      // Create object URL
      const url = window.URL.createObjectURL(blob);
      console.log(`[DOWNLOAD] Object URL created`);

      // Create and trigger download link
      const link = document.createElement("a");
      link.href = url;
      link.download = file.name;
      link.style.display = "none";

      // Add to DOM
      document.body.appendChild(link);

      // Trigger click
      console.log(`[DOWNLOAD] Triggering download for: ${file.name}`);
      link.click();

      // Cleanup after a delay
      setTimeout(() => {
        console.log(`[DOWNLOAD] Cleaning up resources`);
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);

      // Dismiss loading toast and show success
      toast.dismiss(loadingToast);
      toast.success(`${file.name} downloaded successfully!`);

      console.log(`[DOWNLOAD] Download completed for ${file.name}`);
    } catch (error) {
      console.error(`[DOWNLOAD ERROR]`, error);
      console.error(`[DOWNLOAD ERROR] Stack:`, error.stack);

      // Show detailed error message
      let errorMsg = "Download failed";

      if (error.response?.data) {
        // Try to parse error from response
        if (error.response.data instanceof Blob) {
          try {
            const text = await error.response.data.text();
            const errorData = JSON.parse(text);
            errorMsg = errorData.message || errorMsg;
          } catch (e) {
            errorMsg = "Unable to download file";
          }
        } else {
          errorMsg = error.response.data.message || errorMsg;
        }
      } else if (error.message) {
        errorMsg = error.message;
      }

      toast.error(`Failed to download ${file.name}: ${errorMsg}`);
    } finally {
      setDownloading(null);
    }
  };

  const handleFileClick = (file) => {
    if (file.type === "folder") {
      navigate(`/dashboard/${file.id}`);
    } else {
      handleFileDownload(file);
    }
  };

  const handleContextMenu = (e, file) => {
    e.preventDefault();
    setSelectedFile(file);
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
    });
  };

  const filteredFiles = files.filter((file) =>
    file.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getFileIcon = (file) => {
    if (file.type === "folder")
      return <Folder className="w-8 h-8 text-amber-500" />;
    const fileType = getFileType(file.name);
    switch (fileType) {
      case "image":
        return <Image className="w-8 h-8 text-purple-500" />;
      case "pdf":
        return <FileText className="w-8 h-8 text-red-500" />;
      case "doc":
        return <FileText className="w-8 h-8 text-blue-500" />;
      case "video":
        return <Video className="w-8 h-8 text-pink-500" />;
      case "audio":
        return <Music className="w-8 h-8 text-indigo-500" />;
      case "zip":
        return <Archive className="w-8 h-8 text-yellow-500" />;
      default:
        return <File className="w-8 h-8 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <div className="h-8 bg-muted rounded w-1/4 mb-4 animate-pulse"></div>
        </div>
        {viewMode === "grid" ? <FileSkeleton /> : <ListSkeleton />}
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Files</h1>
          <p className="text-muted-foreground">
            {filteredFiles.length}{" "}
            {filteredFiles.length === 1 ? "item" : "items"}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 w-64 bg-accent border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all"
            />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          </div>
          {/* Upload Button */}
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center space-x-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Upload</span>
          </button>
          {/* New Folder Button */}
          <button
            onClick={handleFolderCreate}
            className="flex items-center space-x-2 bg-accent text-accent-foreground px-4 py-2 rounded-lg hover:bg-accent/80 transition-colors"
          >
            <FolderPlus className="w-4 h-4" />
            <span>New Folder</span>
          </button>
          {/* View Toggle */}
          <div className="flex bg-accent rounded-lg p-1">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-2 rounded ${
                viewMode === "grid" ? "bg-background" : "hover:bg-accent/80"
              } transition-colors`}
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-2 rounded ${
                viewMode === "list" ? "bg-background" : "hover:bg-accent/80"
              } transition-colors`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Breadcrumb */}
      <Breadcrumb folderId={folderId} />

      {/* Empty State */}
      {filteredFiles.length === 0 && (
        <div className="text-center py-12">
          <div className="w-24 h-24 mx-auto mb-4 bg-accent rounded-full flex items-center justify-center">
            <Folder className="w-12 h-12 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium mb-2">No files found</h3>
          <p className="text-muted-foreground mb-6">
            {searchQuery
              ? "No files match your search."
              : "Get started by uploading some files."}
          </p>
          <button
            onClick={() => setShowUpload(true)}
            className="bg-primary text-primary-foreground px-6 py-2 rounded-lg hover:bg-primary/90 transition-colors"
          >
            Upload Files
          </button>
        </div>
      )}

      {/* Grid View */}
      {viewMode === "grid" && filteredFiles.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
          {filteredFiles.map((file) => (
            <div
              key={file.id}
              onClick={() => !downloading && handleFileClick(file)}
              onContextMenu={(e) => handleContextMenu(e, file)}
              className={`bg-card border rounded-lg p-4 hover:shadow-lg hover:-translate-y-1 transition-all cursor-pointer group ${
                downloading === file.id ? "opacity-50 pointer-events-none" : ""
              }`}
            >
              <div className="flex items-center justify-center h-24 mb-4">
                {downloading === file.id ? (
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                ) : (
                  getFileIcon(file)
                )}
              </div>
              <h3 className="font-medium truncate mb-1">{file.name}</h3>
              <p className="text-sm text-muted-foreground mb-2">
                {formatDate(file.created_at)}
              </p>
              {file.type !== "folder" && (
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(file.size)}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* List View */}
      {viewMode === "list" && filteredFiles.length > 0 && (
        <div className="space-y-2">
          {filteredFiles.map((file) => (
            <div
              key={file.id}
              onClick={() => !downloading && handleFileClick(file)}
              onContextMenu={(e) => handleContextMenu(e, file)}
              className={`bg-card border rounded-lg p-4 hover:shadow-md transition-all cursor-pointer group flex items-center space-x-4 ${
                downloading === file.id ? "opacity-50 pointer-events-none" : ""
              }`}
            >
              <div className="flex-shrink-0">
                {downloading === file.id ? (
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                ) : (
                  getFileIcon(file)
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-medium truncate">{file.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {formatDate(file.created_at)}
                </p>
              </div>
              {file.type !== "folder" && (
                <div className="text-sm text-muted-foreground">
                  {formatFileSize(file.size)}
                </div>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleContextMenu(e, file);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-accent rounded transition-all"
              >
                <MoreVertical className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUpload && (
        <FileUpload
          onClose={() => setShowUpload(false)}
          onUpload={handleFileUpload}
        />
      )}

      {/* Context Menu */}
      {contextMenu && selectedFile && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          onClose={() => setContextMenu(null)}
        >
          {selectedFile.type !== "folder" && (
            <button
              onClick={() => {
                handleFileDownload(selectedFile);
                setContextMenu(null);
              }}
              disabled={downloading === selectedFile.id}
              className="w-full px-4 py-2 text-left text-sm hover:bg-accent transition-colors flex items-center space-x-2 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              <span>
                {downloading === selectedFile.id
                  ? "Downloading..."
                  : "Download"}
              </span>
            </button>
          )}
          <button
            onClick={() => {
              handleFileDelete(selectedFile);
              setContextMenu(null);
            }}
            className="w-full px-4 py-2 text-left text-sm hover:bg-accent transition-colors flex items-center space-x-2 text-destructive"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete</span>
          </button>
        </ContextMenu>
      )}
    </div>
  );
};
export default DashboardPage;

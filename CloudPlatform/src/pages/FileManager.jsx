import React, { useState } from "react";
import "../styles/filemanager.css";

// Placeholder for icons
const Icon = ({ name, className = "" }) => {
  const iconMap = {
    "upload-cloud": "☁️",
    "file-pdf": "📄",
    "file-docx": "📄",
    "file-png": "🖼️",
    folder: "📁",
    options: "⋮", // Three dots
    close: "✕", // Close/cancel
    "check-circle": "✅", // Green check for complete
    download: "⬇️", // Download icon
    link: "🔗", // For status link
    grid: "▦",
    list: "☰",
    prev: "◀",
    next: "▶",
  };
  return <span className={`icon ${className}`}>{iconMap[name] || name}</span>;
};

// Component for an individual Upload Item in the queue
const UploadItem = ({ file, onCancel, onRetry }) => {
  const progressBarClass = file.progress === 100 ? "green" : "blue";
  const progressText =
    file.progress < 100
      ? `${file.uploadedMB} of ${file.totalMB} MB at ${file.speed}`
      : "Upload complete";

  return (
    <div className="upload-item">
      <Icon name={`file-${file.type.toLowerCase()}`} className="file-icon" />
      <div className="upload-item-content">
        <div className="file-name">{file.name}</div>
        <div className="progress-details">
          <span>{progressText}</span>
          {file.progress < 100 ? (
            <span>{file.progress}%</span>
          ) : (
            <Icon name="check-circle" className="status-icon" />
          )}
        </div>
        <div className="progress-bar-container">
          <div
            className={`progress-bar ${progressBarClass}`}
            style={{ width: `${file.progress}%` }}
          ></div>
        </div>
      </div>
      <div className="upload-actions">
        {
          file.progress < 100 ? (
            <>
              <button className="action-icon-btn">
                <Icon name="options" /> {/* Pause/Resume or Options */}
              </button>
              <button
                className="action-icon-btn red"
                onClick={() => onCancel(file.id)}
              >
                <Icon name="close" />
              </button>
            </>
          ) : null /* No actions needed for completed upload in this example */
        }
      </div>
    </div>
  );
};

const FileManager = () => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  // Dummy upload queue data
  const uploadQueue = [
    {
      id: 1,
      name: "document_final.pdf",
      type: "PDF",
      progress: 65,
      uploadedMB: "1.2",
      totalMB: "1.8",
      speed: "500 KB/s",
      eta: "2 minutes",
    },
    {
      id: 2,
      name: "project_brief.docx",
      type: "DOCX",
      progress: 100,
      uploadedMB: "1.0",
      totalMB: "1.0",
      speed: "0 KB/s",
      eta: "",
    },
  ];

  // Dummy My Files data
  const myFiles = [
    {
      id: 101,
      name: "Annual_Report_2023.pdf",
      type: "PDF",
      size: "2.5 MB",
      modified: "2 hours ago",
      status: "Link",
      iconType: "pdf",
    },
    {
      id: 102,
      name: "Marketing_Banner_Ad.png",
      type: "PNG",
      size: "850 KB",
      modified: "Yesterday",
      status: "-",
      iconType: "png",
    },
    {
      id: 103,
      name: "Project_Assets",
      type: "Folder",
      size: "12.1 GB",
      modified: "June 10, 2024",
      status: "-",
      iconType: "folder",
    },
  ];

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    console.log("Dropped files:", files);
    // Here you would typically process the files for upload
  };

  const handleFileSelect = (e) => {
    const files = e.target.files;
    console.log("Selected files:", files);
    // Here you would typically process the files for upload
  };

  const handleCheckboxChange = (fileId) => {
    setSelectedFiles((prevSelected) =>
      prevSelected.includes(fileId)
        ? prevSelected.filter((id) => id !== fileId)
        : [...prevSelected, fileId]
    );
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedFiles(myFiles.map((file) => file.id));
    } else {
      setSelectedFiles([]);
    }
  };

  return (
    <div className="file-management-page">
      <h1 className="page-title">File Management</h1>

      {/* --- Drag and Drop Upload Zone --- */}
      <div
        className={`upload-zone ${isDragOver ? "drag-over" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Icon name="upload-cloud" className="upload-icon" />
        <p className="upload-text">Drag and Drop Files Here</p>
        <p className="upload-subtitle">
          Supports multiple files and folders for easy uploading.
        </p>
        <input
          type="file"
          multiple
          style={{ display: "none" }}
          id="file-upload-input"
          onChange={handleFileSelect}
        />
        <label htmlFor="file-upload-input" className="choose-files-btn">
          Choose Files
        </label>
      </div>

      {/* --- Upload Queue --- */}
      <div className="upload-queue-section">
        <div className="queue-header">
          <h2 className="queue-title">Upload Queue</h2>
          <span className="queue-status-text">
            Uploading 1 of 2 files. (ETA: {uploadQueue[0]?.eta || "calculating"}
            )
          </span>
        </div>
        {uploadQueue.map((file) => (
          <UploadItem
            key={file.id}
            file={file}
            onCancel={() => console.log("Cancel", file.id)}
          />
        ))}
      </div>

      {/* --- My Files List --- */}
      <div className="file-list-section">
        <div className="list-header">
          <h2 className="list-title">My Files</h2>
          <div className="list-actions">
            <button className="download-btn">
              <Icon name="download" />
              Download Selected (
              <span className="count">{selectedFiles.length}</span>)
            </button>
            <div className="view-toggle">
              <button className="view-toggle-btn">
                <Icon name="grid" className="icon" />
              </button>
              <button className="view-toggle-btn active">
                <Icon name="list" className="icon" />
              </button>
            </div>
          </div>
        </div>

        <table className="files-table">
          <thead>
            <tr>
              <th className="checkbox-col">
                <input
                  type="checkbox"
                  onChange={handleSelectAll}
                  checked={
                    selectedFiles.length === myFiles.length &&
                    myFiles.length > 0
                  }
                />
              </th>
              <th>Name</th>
              <th>Size</th>
              <th>Last Modified</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {myFiles.map((file) => (
              <tr key={file.id}>
                <td className="checkbox-col">
                  <input
                    type="checkbox"
                    checked={selectedFiles.includes(file.id)}
                    onChange={() => handleCheckboxChange(file.id)}
                  />
                </td>
                <td className="file-name-cell">
                  <Icon
                    name={file.iconType}
                    className={`file-icon ${file.iconType}`}
                  />
                  {file.name}
                </td>
                <td>{file.size}</td>
                <td>{file.modified}</td>
                <td className="status-cell">
                  {file.status === "Link" ? (
                    <a href="#link" className="status-link">
                      <Icon name="link" /> Link
                    </a>
                  ) : (
                    file.status
                  )}
                </td>
                <td>
                  <Icon name="download" className="action-download" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* --- Pagination --- */}
        <div className="pagination-container">
          <span>Showing 1-3 of 100</span>
          <div className="pagination-controls">
            <button className="pagination-btn disabled">Previous</button>
            <button className="pagination-btn active">1</button>
            <button className="pagination-btn">2</button>
            <button className="pagination-btn">3</button>
            <button className="pagination-btn">Next</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileManager;

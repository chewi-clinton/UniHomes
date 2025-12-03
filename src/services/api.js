import axios from "axios";

const API_BASE_URL = "/api";

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Check if it's not an admin route
      if (!error.config.url.includes("/admin/")) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  sendOTP: (email) => api.post("/auth/send-otp", { email }),
  verifyOTP: (email, otp) => api.post("/auth/verify-otp", { email, otp }),
  enroll: (email, name) => api.post("/auth/enroll", { email, name }),
  login: (email) => api.post("/auth/login", { email }),
  logout: () => api.post("/auth/logout"),
};

// Files API
export const filesAPI = {
  listFiles: (folderId) =>
    api.get("/files", { params: folderId ? { folder_id: folderId } : {} }),

  uploadFile: (file, folderId, onProgress) => {
    const formData = new FormData();
    formData.append("file", file);
    if (folderId) {
      formData.append("folder_id", folderId);
    }

    return api.post("/files/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      timeout: 600000, // 10 minutes for large files
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });
  },

  downloadFile: (fileId) => {
    console.log(`[API] Requesting download for file: ${fileId}`);
    return api.get(`/files/download/${fileId}`, {
      responseType: "blob",
      timeout: 600000, // 10 minutes for large files
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          console.log(`[API] Download progress: ${percentCompleted}%`);
        }
      },
    });
  },

  deleteFile: (fileId, permanent = true) =>
    api.delete(`/files/${fileId}`, { params: { permanent } }),

  createFolder: (name, parentFolderId) =>
    api.post("/files/folders", {
      folder_name: name,
      parent_folder_id: parentFolderId,
    }),

  shareFile: (fileId, shareWithEmail, permission = "read") =>
    api.post("/files/share", {
      file_id: fileId,
      share_with_email: shareWithEmail,
      permission,
    }),

  getSharedFiles: () => api.get("/files/shared"),
};

// Storage API
export const storageAPI = {
  getStorageInfo: () => api.get("/storage"),
  getStorageUsage: () => api.get("/storage/usage"),
};

// Admin API
export const adminAPI = {
  // Verify admin key
  verifyAdminKey: (adminKey) =>
    api.post("/admin/verify", { admin_key: adminKey }),

  // Get system status
  getStatus: (adminKey) =>
    api.get("/admin/status", {
      headers: { "X-Admin-Key": adminKey },
    }),

  // List all users
  getUsers: (adminKey) =>
    api.get("/admin/users", {
      headers: { "X-Admin-Key": adminKey },
    }),

  // List all storage nodes
  getNodes: (adminKey) =>
    api.get("/admin/nodes", {
      headers: { "X-Admin-Key": adminKey },
    }),

  // Get user details
  getUserDetails: (adminKey, userId) =>
    api.get(`/admin/users/${userId}`, {
      headers: { "X-Admin-Key": adminKey },
    }),

  // Stream system events (Server-Sent Events)
  getEvents: (adminKey) => {
    return new EventSource(
      `${API_BASE_URL}/admin/events?admin_key=${adminKey}`
    );
  },

  // Node management
  createNode: (adminKey, nodeData) =>
    api.post("/admin/nodes", nodeData, {
      headers: { "X-Admin-Key": adminKey },
    }),

  startNode: (adminKey, nodeId, nodeData) =>
    api.post(`/admin/nodes/${nodeId}/start`, nodeData, {
      headers: { "X-Admin-Key": adminKey },
    }),

  stopNode: (adminKey, nodeId) =>
    api.post(`/admin/nodes/${nodeId}/stop`, null, {
      headers: { "X-Admin-Key": adminKey },
    }),

  deleteNode: (adminKey, nodeId) =>
    api.delete(`/admin/nodes/${nodeId}`, {
      headers: { "X-Admin-Key": adminKey },
    }),
};

export default api;

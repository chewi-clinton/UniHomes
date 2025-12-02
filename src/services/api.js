import axios from "axios";

const API_BASE_URL = "/api";

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
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
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
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
    api.get("/files", { params: folderId ? { folder_id: folderId } : {} }), // FIXED: was folder_id, now folderId
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
  downloadFile: (fileId) =>
    api.get(`/files/download/${fileId}`, {
      responseType: "blob",
    }),
  deleteFile: (fileId, permanent = false) =>
    api.delete(`/files/${fileId}`, { params: { permanent } }),
  createFolder: (name, parentFolderId) =>
    api.post("/folders", { name, parent_folder_id: parentFolderId }),
};

// Storage API
export const storageAPI = {
  getStorageInfo: () => api.get("/storage"),
};

// Admin API
export const adminAPI = {
  getStatus: () => api.get("/admin/status"),
  getUsers: () => api.get("/admin/users"),
  getNodes: () => api.get("/admin/nodes"),
  getEvents: () => {
    const token = localStorage.getItem("auth_token");
    return new EventSource(`${API_BASE_URL}/admin/events`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};

export default api;

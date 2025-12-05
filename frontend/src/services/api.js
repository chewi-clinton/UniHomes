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
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
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
    if (folderId) formData.append("folder_id", folderId);

    return api.post("/files/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 600000,
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percent);
        }
      },
    });
  },

  downloadFile: (fileId) =>
    api.get(`/files/download/${fileId}`, {
      responseType: "blob",
      timeout: 600000,
    }),

  deleteFile: (fileId, permanent = true) =>
    api.delete(`/files/${fileId}`, { params: { permanent } }),

  createFolder: (name, parentFolderId) =>
    api.post("/files/folders", {
      folder_name: name,
      parent_folder_id: parentFolderId || null,
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

// Payment API - FULLY INTEGRATED
export const paymentAPI = {
  getTiers: () => api.get("/payment/tiers"),
  initiatePayment: (tierId, provider, phoneNumber) =>
    api.post("/payment/initiate", {
      tier_id: tierId,
      provider,
      phone_number: phoneNumber,
    }),
  checkStatus: (paymentId) => api.get(`/payment/status/${paymentId}`),
  getHistory: (limit = 50) =>
    api.get("/payment/history", { params: { limit } }),
  cancelPayment: (paymentId) => api.post(`/payment/cancel/${paymentId}`),

  // Admin Payment Endpoints
  getPaymentStats: (adminKey) =>
    api.get("/payment/admin/stats", { headers: { "X-Admin-Key": adminKey } }),

  getAllPayments: (adminKey, limit = 100, statusFilter = "") =>
    api.get("/payment/admin/payments", {
      headers: { "X-Admin-Key": adminKey },
      params: { limit, status: statusFilter || undefined },
    }),
};

// Admin API
export const adminAPI = {
  verifyAdminKey: (adminKey) =>
    api.post("/admin/verify", { admin_key: adminKey }),
  getStatus: (adminKey) =>
    api.get("/admin/status", { headers: { "X-Admin-Key": adminKey } }),
  getUsers: (adminKey) =>
    api.get("/admin/users", { headers: { "X-Admin-Key": adminKey } }),
  getNodes: (adminKey) =>
    api.get("/admin/nodes", { headers: { "X-Admin-Key": adminKey } }),
  getUserDetails: (adminKey, userId) =>
    api.get(`/admin/users/${userId}`, { headers: { "X-Admin-Key": adminKey } }),
  getEvents: (adminKey) =>
    new EventSource(`${API_BASE_URL}/admin/events?admin_key=${adminKey}`),
};

export default api;

import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

// Auth token storage and interceptors removed for simple public access.

// ── Auth API Calls ───────────────────────────────────────────────────────────

export const register = async (username, email, password) => {
  const res = await api.post("/api/v1/auth/register", { username, email, password });
  return res.data;
};

export const login = async (username, password) => {
  const res = await api.post("/api/v1/auth/login", { username, password });
  const token = res.data.access_token;
  setToken(token);
  return res.data;
};

export const logout = () => {
  clearToken();
  window.location.href = "/login";
};

export const getMe = async () => {
  const res = await api.get("/api/v1/auth/me");
  return res.data;
};

// ── Dataset API Calls ────────────────────────────────────────────────────────

export const uploadFile = async (file, onProgress) => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/api/v1/datasets/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total));
    },
  });
  return res.data;
};

export const getProfile = async (filename) => {
  const res = await api.get(`/api/v1/datasets/profile/${encodeURIComponent(filename)}`);
  return res.data;
};

// ── Analysis API Calls ───────────────────────────────────────────────────────

export const submitQueryAsync = async (filename, query) => {
  const res = await api.post("/api/v1/analysis/query/async", { filename, query });
  return res.data;
};

export const pollJobStatus = async (jobId) => {
  const res = await api.get(`/api/v1/analysis/jobs/${jobId}`);
  return res.data;
};

// ── Health Check ─────────────────────────────────────────────────────────────
export const healthCheck = async () => {
  const res = await api.get("/");
  return res.data;
};

// ── Safe Blob Download Helper ──────────────────────────────────────────────
export const downloadChartImage = async (url, filename = 'chart.png') => {
  if (!url) return;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch image blob');
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
  } catch (err) {
    console.warn('Cross-origin blob fetch failed, opening safely in new tab:', err);
    window.open(url, '_blank');
  }
};

export default api;

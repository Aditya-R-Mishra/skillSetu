import axios from "axios";

/**
 * Axios client wired to the FastAPI backend via the Vite dev proxy.
 *
 * HOW THE PROXY WORKS:
 *   Frontend calls  →  /api/auth/login
 *   Vite rewrites   →  http://localhost:8000/auth/login   (strips /api prefix)
 *   Backend sees    →  POST /auth/login
 *
 * This means:
 *   ✅ No hardcoded localhost:8000 in the frontend
 *   ✅ No CORS preflight issues in development
 *   ✅ Swap to production URL in one place (vite.config.js proxy target)
 */
const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 30000, // 30 seconds — Gemini quiz generation can take 5-10s
});

// ── Request Interceptor ────────────────────────────────────────────────────────
// Reads JWT from localStorage and attaches it as Authorization: Bearer <token>
// to every outgoing request automatically. Pages don't need to handle this.
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response Interceptor ───────────────────────────────────────────────────────
// If the backend returns 401 (token expired or invalid):
//   1. Clear stored token + user from localStorage
//   2. Redirect to /login page
// This handles token expiry transparently without any page knowing about it.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (
        !window.location.pathname.startsWith("/login") &&
        !window.location.pathname.startsWith("/register")
      ) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── PDF Upload Helper ──────────────────────────────────────────────────────────
/**
 * Upload a PDF file to POST /materials/upload-pdf.
 *
 * WHY a separate helper?
 * PDF upload uses multipart/form-data (not JSON) because it carries a binary file.
 * Axios automatically sets the correct Content-Type with boundary when passed a
 * FormData object — but only if we don't override Content-Type ourselves.
 * This helper ensures that override is applied correctly every time.
 *
 * Usage:
 *   const formData = new FormData();
 *   formData.append("title", "My PDF Title");
 *   formData.append("competency_area", "Survey Design");
 *   formData.append("file", fileInputRef.current.files[0]);
 *   await uploadPDF(formData);
 */
export const uploadPDF = (formData) =>
  api.post("/materials/upload-pdf", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export default api;
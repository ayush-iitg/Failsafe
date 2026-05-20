/**
 * api.js — Centralised Axios API Layer
 * ======================================
 * All HTTP calls go through this file. Never call axios directly in components.
 *
 * WHY A CENTRALISED API LAYER?
 *  - One place to change the base URL (dev vs prod)
 *  - Auth token automatically attached to every request via interceptor
 *  - Consistent error handling
 *  - Easy to mock in tests
 *
 * INTERVIEW Q: "How do you manage API calls in React?"
 * ANSWER: "I use a centralised Axios instance with request interceptors to
 *          attach JWT tokens and response interceptors to handle 401 errors
 *          globally — redirecting to login if the session expires."
 */

import axios from 'axios'

// ── Create Axios instance ──────────────────────────────────────────────────────
const api = axios.create({
  baseURL: '/api',        // Proxied to http://localhost:8000/api by Vite config
  timeout: 30000,         // 30 second timeout (ML inference can take a moment)
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request Interceptor — attach JWT token ─────────────────────────────────────
// Runs BEFORE every request. Reads token from localStorage and adds it.
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('failsafe_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response Interceptor — handle 401 globally ────────────────────────────────
// Runs AFTER every response. If 401 → token expired → redirect to login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid — clear storage and redirect to login
      localStorage.removeItem('failsafe_token')
      localStorage.removeItem('failsafe_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)


// ═══════════════════════════════════════════════════════════════════════════════
// AUTH API
// ═══════════════════════════════════════════════════════════════════════════════

export const authAPI = {
  login: (email, password) =>
    api.post('/auth/login', { email, password }),

  register: (userData) =>
    api.post('/auth/register', userData),

  getMe: () =>
    api.get('/auth/me'),
}


// ═══════════════════════════════════════════════════════════════════════════════
// UPLOAD API
// ═══════════════════════════════════════════════════════════════════════════════

export const uploadAPI = {
  /**
   * Upload a CSV file of student data.
   * Uses FormData for multipart/form-data (required for file uploads).
   */
  uploadCSV: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}


// ═══════════════════════════════════════════════════════════════════════════════
// DASHBOARD API
// ═══════════════════════════════════════════════════════════════════════════════

export const dashboardAPI = {
  getStats: () =>
    api.get('/dashboard/stats'),

  getRiskDistribution: () =>
    api.get('/dashboard/risk-distribution'),

  getStudents: (page = 1, pageSize = 20, riskFilter = null) => {
    const params = { page, page_size: pageSize }
    if (riskFilter) params.risk_filter = riskFilter
    return api.get('/dashboard/students', { params })
  },
}


// ═══════════════════════════════════════════════════════════════════════════════
// EXPLANATION API
// ═══════════════════════════════════════════════════════════════════════════════

export const explainAPI = {
  getExplanation: (studentId) =>
    api.get(`/explain/${studentId}`),
}


// ═══════════════════════════════════════════════════════════════════════════════
// INTERVENTION API
// ═══════════════════════════════════════════════════════════════════════════════

export const interventionAPI = {
  getIntervention: (studentId) =>
    api.get(`/interventions/${studentId}`),

  markApplied: (interventionId, data) =>
    api.patch(`/interventions/${interventionId}/apply`, data),
}

export default api

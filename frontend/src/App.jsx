/**
 * App.jsx — Root Component with Routing
 * =======================================
 * Defines the URL structure of the entire application.
 * Uses React Router v6 for client-side navigation.
 *
 * ROUTING ARCHITECTURE:
 *  Public routes  → accessible without login (/login)
 *  Protected routes → require valid JWT (everything else)
 *
 * ProtectedRoute component checks localStorage for a token.
 * If no token → redirect to /login automatically.
 *
 * INTERVIEW Q: "How do you protect routes in React?"
 * ANSWER: "I use a wrapper component that checks for a JWT token
 *          in localStorage before rendering. If not present, it
 *          redirects to /login using React Router's <Navigate>."
 */

import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import AnalyticsPage from './pages/AnalyticsPage'
import StudentDetailPage from './pages/StudentDetailPage'
import InterventionPage from './pages/InterventionPage'
import Layout from './components/Layout'

/**
 * ProtectedRoute — wraps any route that requires authentication.
 * Checks for token in localStorage. If missing → redirect to /login.
 */
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('failsafe_token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public route */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes — all wrapped in Layout (sidebar + navbar) */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          {/* Index route: redirect / → /dashboard */}
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="students/:studentId" element={<StudentDetailPage />} />
          <Route path="interventions/:studentId" element={<InterventionPage />} />
        </Route>

        {/* Catch-all: redirect unknown URLs to dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

/**
 * LoginPage.jsx — Faculty Login Screen
 * ======================================
 * Clean login form with email + password.
 * On success: stores JWT + user profile in localStorage → redirects to dashboard.
 *
 * STATE MANAGEMENT:
 *  Local state (useState) is sufficient here — form data doesn't need to be
 *  shared with other components. No Redux/Context needed for a simple form.
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../api/api'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  const navigate = useNavigate()

  // Form state
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  async function handleLogin(e) {
    e.preventDefault()          // Prevent default browser form submission
    setError('')
    setLoading(true)

    try {
      // 1. Login → get JWT token
      const tokenRes = await authAPI.login(email, password)
      const token = tokenRes.data.access_token
      localStorage.setItem('failsafe_token', token)

      // 2. Fetch current user profile using the token
      const userRes = await authAPI.getMe()
      localStorage.setItem('failsafe_user', JSON.stringify(userRes.data))

      // 3. Navigate to dashboard
      navigate('/dashboard')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed. Please check your credentials.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.logo}>🛡️</div>
          <h1 className={styles.title}>FAILSAFE</h1>
          <p className={styles.subtitle}>Student Failure Risk Prediction System</p>
        </div>

        {/* Error message */}
        {error && <div className="alert alert-error">{error}</div>}

        {/* Login form */}
        <form onSubmit={handleLogin} className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label}>Email Address</label>
            <input
              type="email"
              className="input"
              placeholder="faculty@college.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Password</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '0.75rem' }}
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className={styles.footer}>
          FAILSAFE — Powered by XGBoost + SHAP Explainable AI
        </p>
      </div>
    </div>
  )
}

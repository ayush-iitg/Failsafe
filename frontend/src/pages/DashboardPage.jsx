/**
 * DashboardPage.jsx — Main Faculty Dashboard
 * ============================================
 * Shows KPI cards + student risk table.
 * Data fetched on mount using useEffect.
 *
 * REACT DATA FETCHING PATTERN:
 *  useEffect with empty dependency array [] = runs once when component mounts.
 *  This is the standard pattern for initial data loading.
 *  In more complex apps you'd use React Query or SWR for caching + refetching.
 */

import React, { useState, useEffect } from 'react'
import { dashboardAPI } from '../api/api'
import KPICard from '../components/KPICard'
import StudentTable from '../components/StudentTable'
import styles from './DashboardPage.module.css'

export default function DashboardPage() {
  const [stats, setStats]         = useState(null)
  const [students, setStudents]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState('')
  const [riskFilter, setRiskFilter] = useState('')
  const [page, setPage]           = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  const user = JSON.parse(localStorage.getItem('failsafe_user') || '{}')

  // Fetch KPI stats on mount
  useEffect(() => {
    dashboardAPI.getStats()
      .then(res => setStats(res.data))
      .catch(() => setError('Failed to load dashboard stats.'))
  }, [])

  // Fetch students when page or filter changes
  useEffect(() => {
    setLoading(true)
    dashboardAPI.getStudents(page, 20, riskFilter || null)
      .then(res => {
        setStudents(res.data.data)
        setTotalPages(res.data.total_pages)
      })
      .catch(() => setError('Failed to load student data.'))
      .finally(() => setLoading(false))
  }, [page, riskFilter])

  return (
    <div className="page-container">
      {/* Page header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Dashboard</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Welcome back, {user.full_name}
          </p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* ── KPI Cards ─────────────────────────────────────────────── */}
      <div className={styles.kpiGrid}>
        <KPICard
          icon="👥"
          title="Total Students"
          value={stats?.total_students ?? '—'}
          subtitle="Across all uploads"
        />
        <KPICard
          icon="🔴"
          title="High Risk"
          value={stats?.high_risk_count ?? '—'}
          subtitle={stats ? `${stats.high_risk_percentage}% of total` : ''}
          variant="danger"
        />
        <KPICard
          icon="🟡"
          title="Medium Risk"
          value={stats?.medium_risk_count ?? '—'}
          subtitle="Needs monitoring"
          variant="warning"
        />
        <KPICard
          icon="🟢"
          title="Low Risk"
          value={stats?.low_risk_count ?? '—'}
          subtitle="On track"
          variant="success"
        />
        <KPICard
          icon="✅"
          title="Interventions Applied"
          value={stats?.interventions_applied ?? '—'}
          subtitle="Faculty actions taken"
        />
      </div>

      {/* ── Student Table ──────────────────────────────────────────── */}
      <div className="card" style={{ marginTop: '2rem' }}>
        <div className={styles.tableHeader}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>Student Risk Overview</h2>
          {/* Risk filter buttons */}
          <div className={styles.filterGroup}>
            {['', 'High', 'Medium', 'Low'].map(f => (
              <button
                key={f}
                className={`btn ${riskFilter === f ? 'btn-primary' : 'btn-ghost'}`}
                style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}
                onClick={() => { setRiskFilter(f); setPage(1) }}
              >
                {f || 'All'}
              </button>
            ))}
          </div>
        </div>

        <StudentTable students={students} loading={loading} />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className={styles.pagination}>
            <button
              className="btn btn-ghost"
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
            >
              ← Prev
            </button>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Page {page} of {totalPages}
            </span>
            <button
              className="btn btn-ghost"
              disabled={page === totalPages}
              onClick={() => setPage(p => p + 1)}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

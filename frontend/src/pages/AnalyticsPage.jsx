/**
 * AnalyticsPage.jsx — Risk Analytics & Charts
 * =============================================
 * Visualises risk distribution using Recharts.
 * Uses PieChart for risk breakdown and BarChart for at-a-glance comparison.
 *
 * WHY RECHARTS?
 *  - Built specifically for React (component-based, not imperative like D3)
 *  - Lightweight compared to Chart.js
 *  - Good enough for dashboard-level charts
 *  - Easy to explain in interviews: "I used Recharts because it follows
 *    React's declarative model — charts are just components."
 */

import React, { useState, useEffect } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { dashboardAPI } from '../api/api'

const RISK_COLOURS = {
  High:   '#ef4444',
  Medium: '#f59e0b',
  Low:    '#10b981',
}

export default function AnalyticsPage() {
  const [distribution, setDistribution] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      dashboardAPI.getRiskDistribution(),
      dashboardAPI.getStats(),
    ]).then(([distRes, statsRes]) => {
      setDistribution(distRes.data)
      setStats(statsRes.data)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="page-container"><div className="spinner" /></div>

  return (
    <div className="page-container">
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        Risk Analytics
      </h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem' }}>
        Overview of student risk distribution across your class.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>

        {/* ── Pie chart ──────────────────────────────────────────── */}
        <div className="card">
          <h3 style={{ marginBottom: '1.25rem', fontSize: '0.95rem', fontWeight: 600 }}>
            Risk Distribution
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={distribution}
                dataKey="count"
                nameKey="label"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ label, percentage }) => `${label} (${percentage}%)`}
              >
                {distribution.map((entry) => (
                  <Cell key={entry.label} fill={RISK_COLOURS[entry.label]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px' }}
                labelStyle={{ color: 'var(--text-primary)' }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* ── Bar chart ──────────────────────────────────────────── */}
        <div className="card">
          <h3 style={{ marginBottom: '1.25rem', fontSize: '0.95rem', fontWeight: 600 }}>
            Student Count by Risk Level
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={distribution} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="label" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px' }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {distribution.map((entry) => (
                  <Cell key={entry.label} fill={RISK_COLOURS[entry.label]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

      </div>

      {/* ── Summary stats ─────────────────────────────────────────── */}
      {stats && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
            Intervention Summary
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--risk-high)' }}>
                {stats.high_risk_count + stats.medium_risk_count}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Students Need Intervention
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--risk-low)' }}>
                {stats.interventions_applied}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Interventions Applied
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent)' }}>
                {stats.high_risk_percentage}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                High Risk Rate
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

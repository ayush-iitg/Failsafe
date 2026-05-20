/**
 * StudentDetailPage.jsx — SHAP Explanation for Individual Student
 * ================================================================
 * Shows the XGBoost prediction + SHAP waterfall explanation for one student.
 *
 * KEY CONCEPT — SHAP Waterfall Chart:
 *  A horizontal bar chart where:
 *  - Bars to the RIGHT (positive) = features that INCREASE failure risk
 *  - Bars to the LEFT  (negative) = features that DECREASE failure risk
 *  - Length = magnitude of contribution
 *
 *  This is what makes the system EXPLAINABLE — faculty can see exactly
 *  WHY a student was flagged, not just that they were flagged.
 */

import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { explainAPI } from '../api/api'
import RiskBadge from '../components/RiskBadge'

export default function StudentDetailPage() {
  const { studentId } = useParams()   // Extract :studentId from the URL
  const navigate      = useNavigate()
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState('')

  useEffect(() => {
    explainAPI.getExplanation(studentId)
      .then(res => setExplanation(res.data))
      .catch(err => setError(err.response?.data?.detail || 'Failed to load explanation.'))
      .finally(() => setLoading(false))
  }, [studentId])

  if (loading) return <div className="page-container"><div className="spinner" /></div>
  if (error) return <div className="page-container"><div className="alert alert-error">{error}</div></div>
  if (!explanation) return null

  // Prepare chart data — sort by absolute SHAP value
  const chartData = explanation.top_features.map(f => ({
    name: f.feature,
    value: f.shap_value,
    direction: f.direction,
  }))

  return (
    <div className="page-container">
      {/* Back button */}
      <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ marginBottom: '1.5rem' }}>
        ← Back
      </button>

      {/* Student header */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              Student #{studentId} — Risk Explanation
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
              XGBoost prediction with SHAP explainability
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <RiskBadge label={explanation.risk_label} />
            <span style={{
              fontSize: '1.75rem', fontWeight: 700,
              color: explanation.risk_label === 'High' ? 'var(--risk-high)'
                   : explanation.risk_label === 'Medium' ? 'var(--risk-medium)'
                   : 'var(--risk-low)'
            }}>
              {(explanation.risk_score * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Explanation sentence */}
      <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--accent-soft)', border: '1px solid rgba(79,142,247,0.3)' }}>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
          <span style={{ fontSize: '1.25rem' }}>🧠</span>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
              AI Explanation
            </div>
            <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem', lineHeight: 1.6 }}>
              {explanation.explanation_text}
            </p>
          </div>
        </div>
      </div>

      {/* SHAP Waterfall Chart */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem' }}>
          SHAP Feature Contributions
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Positive values (→) increase risk. Negative values (←) decrease risk.
          Base prediction: {(explanation.base_value * 100).toFixed(1)}%
        </p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 160, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
              tickFormatter={v => v.toFixed(2)}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: 'var(--text-primary)', fontSize: 11 }}
              width={155}
            />
            <ReferenceLine x={0} stroke="var(--border-strong)" />
            <Tooltip
              formatter={(v) => [v.toFixed(4), 'SHAP Value']}
              contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px' }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={entry.value > 0 ? '#ef4444' : '#10b981'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Feature table */}
      <div className="card">
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
          Top Contributing Factors
        </h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>SHAP Value</th>
                <th>Impact</th>
              </tr>
            </thead>
            <tbody>
              {explanation.top_features.map((f, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{f.feature}</td>
                  <td style={{ fontFamily: 'monospace' }}>{f.shap_value.toFixed(4)}</td>
                  <td>
                    <span className={`badge ${f.direction === 'increases_risk' ? 'badge-high' : 'badge-low'}`}>
                      {f.direction === 'increases_risk' ? '↑ Increases Risk' : '↓ Decreases Risk'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <button
          className="btn btn-primary"
          style={{ marginTop: '1.25rem' }}
          onClick={() => navigate(`/interventions/${studentId}`)}
        >
          View Intervention Plan →
        </button>
      </div>
    </div>
  )
}

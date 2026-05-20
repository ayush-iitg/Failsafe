/**
 * InterventionPage.jsx — Personalised Intervention Plan
 * =======================================================
 * Displays the rule-based intervention recommendations for a student.
 * Faculty can mark the plan as applied and add notes.
 */

import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { interventionAPI } from '../api/api'
import RiskBadge from '../components/RiskBadge'

const PRIORITY_ICONS = { High: '🔴', Medium: '🟡', Low: '🟢' }

export default function InterventionPage() {
  const { studentId } = useParams()
  const navigate      = useNavigate()

  const [intervention, setIntervention] = useState(null)
  const [loading, setLoading]           = useState(true)
  const [saving, setSaving]             = useState(false)
  const [error, setError]               = useState('')
  const [notes, setNotes]               = useState('')
  const [applied, setApplied]           = useState(false)
  const [saved, setSaved]               = useState(false)

  useEffect(() => {
    interventionAPI.getIntervention(studentId)
      .then(res => {
        setIntervention(res.data)
        setApplied(res.data.is_applied)
        setNotes(res.data.faculty_notes || '')
      })
      .catch(err => setError(err.response?.data?.detail || 'No intervention plan found.'))
      .finally(() => setLoading(false))
  }, [studentId])

  async function handleSave() {
    setSaving(true)
    try {
      const res = await interventionAPI.markApplied(intervention.id, {
        is_applied: applied,
        faculty_notes: notes,
      })
      setIntervention(res.data)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)  // Auto-hide success message
    } catch {
      setError('Failed to save. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="page-container"><div className="spinner" /></div>

  return (
    <div className="page-container">
      <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ marginBottom: '1.5rem' }}>
        ← Back
      </button>

      <h1 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>
        Intervention Plan — Student #{studentId}
      </h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '2rem' }}>
        Auto-generated based on SHAP risk factors. Review and apply below.
      </p>

      {error && <div className="alert alert-error">{error}</div>}
      {saved  && <div className="alert alert-success">✅ Intervention plan saved successfully.</div>}

      {intervention && (
        <>
          {/* Priority badge */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Priority Level
                </span>
                <div style={{ marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1.25rem' }}>{PRIORITY_ICONS[intervention.priority]}</span>
                  <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{intervention.priority} Priority</span>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status</span>
                <div style={{ marginTop: '0.25rem' }}>
                  <span className={`badge ${intervention.is_applied ? 'badge-low' : 'badge-medium'}`}>
                    {intervention.is_applied ? '✅ Applied' : '⏳ Pending'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Recommended actions */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
              Recommended Actions
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {intervention.actions.map((action, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    gap: '0.75rem',
                    padding: '0.875rem 1rem',
                    background: 'var(--bg-secondary)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border)',
                  }}
                >
                  <span style={{ color: 'var(--accent)', fontWeight: 700, flexShrink: 0 }}>
                    {i + 1}.
                  </span>
                  <span style={{ color: 'var(--text-primary)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                    {action}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Faculty notes + apply toggle */}
          <div className="card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '1rem' }}>
              Faculty Response
            </h3>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={applied}
                  onChange={e => setApplied(e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--risk-low)' }}
                />
                <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                  Mark intervention as applied
                </span>
              </label>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.4rem' }}>
                Notes (optional)
              </label>
              <textarea
                className="input"
                rows={3}
                placeholder="Add any notes about the intervention applied..."
                value={notes}
                onChange={e => setNotes(e.target.value)}
                style={{ resize: 'vertical' }}
              />
            </div>

            <button
              className="btn btn-primary"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving...' : '💾 Save Plan'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

/**
 * StudentTable.jsx — Reusable Student Data Table
 * ================================================
 * Displays paginated list of students with their risk predictions.
 * Clicking a row navigates to the student detail/explanation page.
 *
 * Props:
 *  students  — array of {student, prediction} objects
 *  loading   — boolean
 */

import React from 'react'
import { useNavigate } from 'react-router-dom'
import RiskBadge from './RiskBadge'

export default function StudentTable({ students = [], loading = false }) {
  const navigate = useNavigate()

  if (loading) return <div className="spinner" />

  if (!students.length) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
        No students found. Upload a CSV to get started.
      </div>
    )
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Student</th>
            <th>Age</th>
            <th>Study Time</th>
            <th>Absences</th>
            <th>Failures</th>
            <th>G1</th>
            <th>G2</th>
            <th>Risk</th>
            <th>Score</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {students.map(({ student, prediction }, idx) => (
            <tr key={student.id}>
              <td style={{ color: 'var(--text-muted)' }}>{idx + 1}</td>
              <td>
                <span style={{ fontWeight: 500 }}>
                  {student.student_name || `Student #${student.id}`}
                </span>
              </td>
              <td>{student.age ?? '—'}</td>
              <td>{student.studytime ?? '—'}</td>
              <td>{student.absences ?? '—'}</td>
              <td>{student.failures ?? '—'}</td>
              <td>{student.G1 ?? '—'}</td>
              <td>{student.G2 ?? '—'}</td>
              <td>
                {prediction
                  ? <RiskBadge label={prediction.risk_label} />
                  : <span style={{ color: 'var(--text-muted)' }}>—</span>
                }
              </td>
              <td>
                {prediction
                  ? <span style={{ fontWeight: 600, color: getRiskColour(prediction.risk_label) }}>
                      {(prediction.risk_score * 100).toFixed(1)}%
                    </span>
                  : '—'
                }
              </td>
              <td>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-ghost"
                    style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}
                    onClick={() => navigate(`/students/${student.id}`)}
                  >
                    Explain
                  </button>
                  {prediction?.risk_label !== 'Low' && (
                    <button
                      className="btn btn-primary"
                      style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}
                      onClick={() => navigate(`/interventions/${student.id}`)}
                    >
                      Intervene
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function getRiskColour(label) {
  if (label === 'High') return 'var(--risk-high)'
  if (label === 'Medium') return 'var(--risk-medium)'
  return 'var(--risk-low)'
}

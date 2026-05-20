/**
 * RiskBadge.jsx — Risk Level Badge
 * ==================================
 * Displays a colour-coded risk label pill.
 * Used in tables and student cards throughout the dashboard.
 *
 * Props:
 *  label — 'High' | 'Medium' | 'Low'
 */

import React from 'react'

export default function RiskBadge({ label }) {
  const variantMap = {
    High:   'badge-high',
    Medium: 'badge-medium',
    Low:    'badge-low',
  }
  const cls = variantMap[label] || 'badge-low'
  return <span className={`badge ${cls}`}>{label}</span>
}

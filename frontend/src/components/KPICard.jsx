/**
 * KPICard.jsx — Key Performance Indicator Card
 * ==============================================
 * Reusable card for displaying a single metric on the dashboard.
 * 
 * Props:
 *  title    — card label, e.g. "High Risk Students"
 *  value    — the number/value to display, e.g. "23"
 *  subtitle — secondary info, e.g. "18.4% of total"
 *  icon     — emoji icon
 *  variant  — 'default' | 'danger' | 'warning' | 'success'
 */

import React from 'react'
import styles from './KPICard.module.css'

export default function KPICard({ title, value, subtitle, icon, variant = 'default' }) {
  return (
    <div className={`card ${styles.card} ${styles[variant]}`}>
      <div className={styles.header}>
        <span className={styles.icon}>{icon}</span>
        <span className={styles.title}>{title}</span>
      </div>
      <div className={styles.value}>{value}</div>
      {subtitle && <div className={styles.subtitle}>{subtitle}</div>}
    </div>
  )
}

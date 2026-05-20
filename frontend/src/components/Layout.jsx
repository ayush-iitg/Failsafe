/**
 * Layout.jsx — App Shell (Sidebar + Top Bar + Page Content)
 * ===========================================================
 * This component is the visual wrapper for all authenticated pages.
 * It renders the sidebar navigation and the <Outlet /> which React Router
 * fills with the current page component.
 *
 * <Outlet /> is a React Router v6 concept — it's a placeholder where
 * child route components are rendered.
 */

import React, { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import styles from './Layout.module.css'

// Navigation items — icon (emoji for simplicity), label, and path
const NAV_ITEMS = [
  { icon: '📊', label: 'Dashboard',   path: '/dashboard' },
  { icon: '📤', label: 'Upload Data', path: '/upload' },
  { icon: '📈', label: 'Analytics',   path: '/analytics' },
]

export default function Layout() {
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('failsafe_user') || '{}')

  function handleLogout() {
    localStorage.removeItem('failsafe_token')
    localStorage.removeItem('failsafe_user')
    navigate('/login')
  }

  return (
    <div className={styles.shell}>
      {/* ── Sidebar ──────────────────────────────────────────────── */}
      <aside className={styles.sidebar}>
        {/* Logo */}
        <div className={styles.logo}>
          <span className={styles.logoIcon}>🛡️</span>
          <span className={styles.logoText}>FAILSAFE</span>
        </div>

        {/* Nav links */}
        <nav className={styles.nav}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.navItemActive : ''}`
              }
            >
              <span className={styles.navIcon}>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User info + logout */}
        <div className={styles.sidebarFooter}>
          <div className={styles.userInfo}>
            <div className={styles.avatar}>
              {user.full_name?.charAt(0)?.toUpperCase() || 'F'}
            </div>
            <div>
              <div className={styles.userName}>{user.full_name || 'Faculty'}</div>
              <div className={styles.userRole}>{user.role || 'faculty'}</div>
            </div>
          </div>
          <button className={`btn btn-ghost ${styles.logoutBtn}`} onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main content area ──────────────────────────────────────── */}
      <main className={styles.main}>
        <Outlet />  {/* React Router renders the current page here */}
      </main>
    </div>
  )
}

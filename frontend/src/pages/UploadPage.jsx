/**
 * UploadPage.jsx — CSV Upload Interface
 * =======================================
 * Faculty drag-and-drop (or click-to-select) CSV upload.
 * Shows upload progress, result summary, and error messages.
 */

import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadAPI } from '../api/api'
import styles from './UploadPage.module.css'

const REQUIRED_COLUMNS = [
  'studytime', 'failures', 'absences', 'G1', 'G2',
  'higher', 'internet', 'schoolsup', 'goout', 'health'
]

export default function UploadPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [file, setFile]         = useState(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)
  const [error, setError]       = useState('')

  function handleFileSelect(selectedFile) {
    if (!selectedFile) return
    if (!selectedFile.name.endsWith('.csv')) {
      setError('Only .csv files are accepted.')
      return
    }
    setFile(selectedFile)
    setError('')
    setResult(null)
  }

  // Drag and drop handlers
  function onDragOver(e) { e.preventDefault(); setDragging(true) }
  function onDragLeave()  { setDragging(false) }
  function onDrop(e)      { e.preventDefault(); setDragging(false); handleFileSelect(e.dataTransfer.files[0]) }

  async function handleUpload() {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const res = await uploadAPI.uploadCSV(file)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please check your CSV format.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-container">
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        Upload Student Data
      </h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.9rem' }}>
        Upload a CSV file containing student records. The system will automatically predict failure risk and generate intervention plans.
      </p>

      {/* ── Drop zone ─────────────────────────────────────────────── */}
      <div
        className={`${styles.dropZone} ${dragging ? styles.dragging : ''} ${file ? styles.hasFile : ''}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={(e) => handleFileSelect(e.target.files[0])}
        />
        <div className={styles.dropIcon}>{file ? '📄' : '📤'}</div>
        {file ? (
          <>
            <p className={styles.fileName}>{file.name}</p>
            <p className={styles.fileSize}>{(file.size / 1024).toFixed(1)} KB</p>
          </>
        ) : (
          <>
            <p className={styles.dropText}>Drag & drop your CSV here</p>
            <p className={styles.dropSubtext}>or click to browse files</p>
          </>
        )}
      </div>

      {/* ── Required columns info ──────────────────────────────────── */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
          Required CSV Columns
        </h3>
        <div className={styles.columnGrid}>
          {REQUIRED_COLUMNS.map(col => (
            <span key={col} className={styles.columnTag}>{col}</span>
          ))}
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>
          Based on UCI Student Performance Dataset format. Download a{' '}
          <span style={{ color: 'var(--accent)', cursor: 'pointer' }}>sample template</span>.
        </p>
      </div>

      {error && <div className="alert alert-error" style={{ marginTop: '1rem' }}>{error}</div>}

      {/* ── Upload button ──────────────────────────────────────────── */}
      <button
        className="btn btn-primary"
        style={{ marginTop: '1.5rem', padding: '0.75rem 2rem' }}
        disabled={!file || loading}
        onClick={handleUpload}
      >
        {loading ? 'Processing...' : '🚀 Upload & Predict'}
      </button>

      {/* ── Results ───────────────────────────────────────────────── */}
      {result && (
        <div className={`card ${styles.resultCard}`}>
          <h3 style={{ marginBottom: '1rem', color: 'var(--risk-low)' }}>
            ✅ Upload Successful
          </h3>
          <div className={styles.resultGrid}>
            <div className={styles.resultStat}>
              <div className={styles.resultNumber}>{result.students_processed}</div>
              <div className={styles.resultLabel}>Students Processed</div>
            </div>
            <div className={styles.resultStat}>
              <div className={styles.resultNumber} style={{ color: 'var(--risk-high)' }}>{result.high_risk}</div>
              <div className={styles.resultLabel}>High Risk</div>
            </div>
            <div className={styles.resultStat}>
              <div className={styles.resultNumber} style={{ color: 'var(--risk-medium)' }}>{result.medium_risk}</div>
              <div className={styles.resultLabel}>Medium Risk</div>
            </div>
            <div className={styles.resultStat}>
              <div className={styles.resultNumber} style={{ color: 'var(--risk-low)' }}>{result.low_risk}</div>
              <div className={styles.resultLabel}>Low Risk</div>
            </div>
          </div>
          <button
            className="btn btn-primary"
            style={{ marginTop: '1.25rem' }}
            onClick={() => navigate('/dashboard')}
          >
            View Dashboard →
          </button>
        </div>
      )}
    </div>
  )
}

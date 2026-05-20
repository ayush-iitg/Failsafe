/**
 * main.jsx — React Application Entry Point
 * ==========================================
 * Mounts the React component tree into the #root div in index.html.
 * This is the first JS file executed by the browser.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/global.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* StrictMode: warns about deprecated patterns in development. No effect in production. */}
    <App />
  </React.StrictMode>
)

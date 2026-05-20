import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Vite Configuration
 * 
 * proxy: forwards /api/* requests from React (port 5173) to FastAPI (port 8000)
 * This avoids CORS issues during development — browser sees one origin.
 * In production, use Nginx to proxy or configure CORS on the server.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // Auth endpoints
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Agent endpoints
      '/agents': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // DTN Bundle System API
      '/api/dtn': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/dtn/, '')
      },
      // ValueFlows Node API
      '/api/vf': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      // Bridge Management API
      '/api/bridge': {
        target: 'http://localhost:8002/bridge',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/bridge/, '')
      },
      // Fallback for any other /api requests to primary service
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 3000,
    proxy: {
      // Auth endpoints
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Agent endpoints
      '/agents': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Fallback for any other /api requests
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

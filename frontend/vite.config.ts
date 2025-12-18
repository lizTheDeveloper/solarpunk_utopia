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
      '/api/dtn': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/dtn/, '')
      },
      '/api/vf': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/vf/, '')
      },
      '/api/bridge': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/bridge/, '')
      },
      '/api/discovery': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/discovery/, '')
      },
      '/api/files': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/files/, '')
      },
    },
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/documents': 'http://localhost:8000',
      '/calculate': 'http://localhost:8000',
      '/ask': 'http://localhost:8000',
      '/ask-document': 'http://localhost:8000',
      '/rag': 'http://localhost:8000',
      '/graph': 'http://localhost:8000',
    }
  },
})

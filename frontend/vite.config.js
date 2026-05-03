import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/recommend': 'http://localhost:8000',
      '/health':    'http://localhost:8000',
      '/export':    'http://localhost:8000',
      '/signup':    'http://localhost:8000',
      '/token':     'http://localhost:8000',
      '/user':      'http://localhost:8000',
    }
  }
})
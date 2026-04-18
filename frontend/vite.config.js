import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  envDir: '../',
  define: {
    'process.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || '/api'),
  },

  server: {
    host: true,
    port: 5173
  },

  preview: {
    host: true,
    allowedHosts: true,
    port: 5173
  }
})
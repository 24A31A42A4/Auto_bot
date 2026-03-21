import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  envDir: '../',

  server: {
    host: true
  },

  preview: {
    host: true,
    allowedHosts: [
      'autobot-form-filler-vijay.up.railway.app'
    ]
  }
})
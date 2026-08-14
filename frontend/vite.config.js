import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Pin the dev server to one predictable port. Without strictPort, Vite
    // silently moves to 5174, 5175 and so on when 5173 is taken, which then
    // fails CORS against a backend that only expects 5173. strictPort makes
    // it fail loudly instead, so a stray leftover server is obvious rather
    // than causing a confusing "cannot reach the backend" later.
    port: 5173,
    strictPort: true,
  },
})

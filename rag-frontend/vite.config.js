import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  server: {
    // Vercel passes the port as an environment variable.
    // We use it if available, otherwise fall back to 5173.
    port: process.env.PORT ? Number(process.env.PORT) : 5173,
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/route': 'http://localhost:8080',
      '/dashboard': 'http://localhost:8080',
      '/metrics': 'http://localhost:8080',
      '/server-2-metrics': {
        target: 'https://a5a3-2600-6c64-623f-76f6-e955-1de0-2335-545e.ngrok-free.app',
        changeOrigin: true,
        secure: true,
        rewrite: () => '/metrics',
        headers: {
          'ngrok-skip-browser-warning': 'true',
        },
      },
    },
  },
})

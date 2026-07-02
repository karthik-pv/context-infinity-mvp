import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/v1': 'http://localhost:8000',
      '/prompt-refinement': 'http://localhost:8000',
      '/project/': 'http://localhost:8000',
    },
  },
})

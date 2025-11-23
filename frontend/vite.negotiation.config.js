import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    open: '/negotiation.html',
  },
  build: {
    rollupOptions: {
      input: {
        negotiation: resolve(__dirname, 'negotiation.html'),
      },
    },
  },
})


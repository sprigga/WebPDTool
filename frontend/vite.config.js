import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  // root: '.', // Set the project root to current directory (修改: Vite 會自動從根目錄尋找 index.html)
  publicDir: 'public', // Explicitly set the public directory
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:9100',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist'
    // Don't explicitly specify input, let Vite auto-detect index.html from public dir
  }
})

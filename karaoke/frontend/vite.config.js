import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  // 部署到 GitHub Pages 子路徑時由 VITE_BASE_PATH 指定（例如 /sanchuan-app/karaoke/），
  // 本機開發環境不需設定，預設為根路徑。
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react()],
})

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // 저장소 루트의 .env 하나를 백엔드와 함께 쓴다. VITE_로 시작하는 값만 브라우저에 들어간다.
  envDir: '..',
})

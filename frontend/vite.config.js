// Vite — это современный инструмент сборки фронтенда.
// Заменяет старый webpack: быстрее запускается и собирает проект.
// Этот файл настраивает как Vite работает с нашим проектом.
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [
    // Подключаем плагин для поддержки однофайловых компонентов Vue (.vue файлы).
    // Без этого плагина Vite не знает как обрабатывать .vue файлы.
    vue()
  ],

  server: {
    // Порт на котором запускается фронтенд в режиме разработки.
    // Открывается по адресу http://localhost:5173
    port: 5173,

    proxy: {
      // Проксирование API-запросов к Django бекенду.
      // Когда Vue делает запрос на /api/..., Vite перенаправляет его
      // на http://localhost:8000/api/... — туда где работает Django.
      // Это решает проблему CORS в режиме разработки.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,  // меняем заголовок Host на localhost:8000
      },
      // Проксирование медиафайлов (загруженные изображения и документы)
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Проксирование WebSocket-соединений.
      // ws://localhost:5173/ws/... → ws://localhost:8000/ws/...
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,  // указываем что это WebSocket, а не обычный HTTP
      },
    },
  },
})
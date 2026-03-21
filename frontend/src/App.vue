<template>
  <div class="app">

    <!-- ===== Шапка сайта ===== -->
    <header class="app-header">
      <h1>💬 SPA Коментарі</h1>
      <p class="subtitle">Залишайте коментарі та відповідайте на інших</p>
    </header>

    <main class="app-main">

      <!-- ===== Панель действий ===== -->
      <div class="actions-bar">
        <!-- Кнопка открывает модальное окно с формой нового комментария -->
        <button class="btn btn-primary" @click="openForm(null)">
          + Новий коментар
        </button>

        <!-- Индикатор WebSocket-соединения.
             v-if/v-else переключает между "Live" и "Offline" в зависимости
             от состояния wsConnected. Зелёный = соединение есть,
             красный = соединение разорвано (идёт переподключение). -->
        <span v-if="wsConnected" class="ws-badge ws-online">● Live</span>
        <span v-else class="ws-badge ws-offline">● Offline</span>
      </div>

      <!-- ===== Список комментариев =====
           Передаём данные вниз через props, получаем события наверх через emit.
           @reply       — пользователь нажал "Відповісти" на комментарии
           @sort        — пользователь кликнул на заголовок колонки
           @page-change — пользователь переключил страницу пагинации -->
      <CommentList
        :comments="comments"
        :total="total"
        :current-page="currentPage"
        :total-pages="totalPages"
        :sort-by="sortBy"
        :sort-order="sortOrder"
        :loading="loading"
        @reply="openForm"
        @sort="handleSort"
        @page-change="handlePageChange"
      />

    </main>

    <!-- ===== Модальное окно с формой =====
         v-if="showForm" — показываем только когда нужна форма.
         @click.self="closeForm" — клик по тёмному фону закрывает модалку.
         .self означает что событие должно произойти именно на этом элементе,
         а не на дочерних (чтобы клик по форме не закрывал модалку). -->
    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <!-- Заголовок меняется в зависимости от того,
               создаём новый коментарий или отвечаем на существующий -->
          <h2>{{ formParentId ? 'Відповідь на коментар' : 'Новий коментар' }}</h2>
          <button class="modal-close" @click="closeForm">✕</button>
        </div>

        <!-- Форма создания комментария.
             :parent-id — ID родительского комментария (null для корневых).
             @submitted — форма успешно отправлена, закрываем модалку.
             @cancel    — пользователь нажал "Скасувати". -->
        <CommentForm
          :parent-id="formParentId"
          @submitted="onCommentSubmitted"
          @cancel="closeForm"
        />
      </div>
    </div>

    <!-- ===== Lightbox для просмотра файлов =====
         Показывается когда пользователь кликает на прикреплённое изображение
         или текстовый файл в комментарии.
         lightbox содержит: { type: 'image'|'text', url/content: '...' }
         @click="lightbox = null" — клик по тёмному фону закрывает lightbox.
         @click.stop на контенте — останавливает всплытие события,
         чтобы клик по картинке не закрывал lightbox. -->
    <div v-if="lightbox" class="lightbox-overlay" @click="lightbox = null">
      <div class="lightbox-content" @click.stop>
        <button class="lightbox-close" @click="lightbox = null">✕</button>
        <!-- Показываем картинку или текст в зависимости от типа файла -->
        <img v-if="lightbox.type === 'image'" :src="lightbox.url" alt="preview" />
        <pre v-else class="lightbox-text">{{ lightbox.content }}</pre>
      </div>
    </div>

  </div>
</template>

<script setup>
// ref()      — реактивная переменная (при изменении Vue обновляет шаблон)
// onMounted  — хук: вызывается когда компонент добавлен в DOM
// onUnmounted— хук: вызывается перед удалением компонента из DOM
// provide    — передаёт данные/функции всем дочерним компонентам
//              без необходимости передавать через props на каждом уровне
import { ref, onMounted, onUnmounted, provide } from 'vue'

import api from './api/comments.js'
import CommentList from './components/CommentList.vue'
import CommentForm from './components/CommentForm.vue'

// ==================== СОСТОЯНИЕ ====================

const comments    = ref([])   // массив комментариев текущей страницы
const total       = ref(0)    // общее количество комментариев в БД
const currentPage = ref(1)    // текущая страница пагинации
const totalPages  = ref(1)    // всего страниц
const sortBy      = ref('created_at') // поле сортировки
const sortOrder   = ref('desc')       // направление: desc = новые первые
const loading     = ref(false)        // true пока загружаем данные
const showForm     = ref(false)       // показывать ли модальное окно формы
const formParentId = ref(null)        // ID родителя (null = новый корневой коментарий)
const wsConnected  = ref(false)       // статус WebSocket-соединения
const lightbox     = ref(null)        // данные для Lightbox или null

// ==================== LIGHTBOX ====================

// provide() делает функцию openLightbox доступной всем дочерним компонентам
// через inject('openLightbox') — без необходимости передавать через props.
// CommentItem и CommentList используют её для открытия Lightbox.
provide('openLightbox', (data) => { lightbox.value = data })

// ==================== WEBSOCKET ====================

let socket = null // ссылка на WebSocket-соединение

function connectWebSocket() {
  // Определяем протокол: wss для https, ws для http
  const wsUrl = `ws://${window.location.host}/ws/comments/`
  socket = new WebSocket(wsUrl)

  // Соединение установлено — показываем индикатор "Live"
  socket.onopen = () => { wsConnected.value = true }

  // Получено сообщение от сервера
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)

    // Если это новый корневой комментарий (без родителя) —
    // добавляем его в начало списка без перезагрузки страницы.
    // Условие: мы на первой странице И сортировка по убыванию даты.
    if (data.type === 'new_comment' && data.comment.parent === null) {
      if (currentPage.value === 1 && sortOrder.value === 'desc') {
        comments.value.unshift(data.comment) // добавляем в начало массива
        total.value += 1
      }
    }
  }

  // Соединение закрыто — показываем "Offline" и переподключаемся через 3 сек
  socket.onclose = () => {
    wsConnected.value = false
    setTimeout(connectWebSocket, 3000)
  }

  // При ошибке закрываем соединение (onclose обработает переподключение)
  socket.onerror = () => { socket.close() }
}

// ==================== ЗАГРУЗКА ДАННЫХ ====================

async function loadComments() {
  loading.value = true
  try {
    // GET /api/comments/?page=1&sort_by=created_at&sort_order=desc
    const res = await api.getComments({
      page:       currentPage.value,
      sort_by:    sortBy.value,
      sort_order: sortOrder.value,
    })
    comments.value  = res.data.results  // массив комментариев страницы
    total.value     = res.data.count    // общее количество
    // Вычисляем количество страниц: делим общее кол-во на размер страницы (25)
    totalPages.value = Math.ceil(res.data.count / 25)
  } catch (err) {
    console.error('Помилка завантаження коментарів:', err)
  } finally {
    // finally выполняется всегда — и при успехе и при ошибке
    loading.value = false
  }
}

// ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

// Открыть форму. parentId — ID комментария на который отвечаем,
// или null если создаём новый корневой комментарий.
function openForm(parentId) {
  formParentId.value = parentId
  showForm.value = true
}

// Закрыть модальное окно и сбросить parentId
function closeForm() {
  showForm.value = false
  formParentId.value = null
}

// Вызывается после успешной отправки формы.
// Закрываем форму, возвращаемся на первую страницу и перезагружаем список.
async function onCommentSubmitted() {
  closeForm()
  currentPage.value = 1
  await loadComments()
}

// Обработчик клика на заголовок колонки таблицы.
// field — поле ('user_name', 'email', 'created_at')
// order — направление ('asc' или 'desc')
function handleSort({ field, order }) {
  sortBy.value    = field
  sortOrder.value = order
  currentPage.value = 1  // при смене сортировки всегда возвращаемся на стр. 1
  loadComments()
}

// Обработчик переключения страницы пагинации
function handlePageChange(page) {
  currentPage.value = page
  loadComments()
  // Плавно прокручиваем страницу вверх
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ==================== ЖИЗНЕННЫЙ ЦИКЛ ====================

// onMounted — вызывается когда компонент добавлен в DOM и готов к работе.
// Загружаем комментарии и подключаемся к WebSocket.
onMounted(() => {
  loadComments()
  connectWebSocket()
})

// onUnmounted — вызывается перед удалением компонента.
// Закрываем WebSocket чтобы не было утечки памяти.
onUnmounted(() => {
  if (socket) socket.close()
})
</script>

<style>
/* ===== Глобальні стилі — застосовуються до всієї сторінки ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: #f0f2f5;
  color: #333;
  min-height: 100vh;
}

.app {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 16px 40px;
}

/* ===== Шапка з градієнтом ===== */
.app-header {
  background: linear-gradient(135deg, #4f8ef7, #6c5ce7);
  color: #fff;
  padding: 28px 32px;
  margin-bottom: 24px;
  border-radius: 0 0 16px 16px;
  box-shadow: 0 4px 16px rgba(79, 142, 247, 0.3);
}
.app-header h1 { font-size: 2rem; }
.subtitle { opacity: 0.85; margin-top: 4px; }

/* ===== Панель дій ===== */
.actions-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.ws-badge { font-size: 0.8rem; font-weight: 600; }
.ws-online  { color: #27ae60; }
.ws-offline { color: #e74c3c; }

/* ===== Кнопки ===== */
.btn {
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  transition: opacity 0.2s, transform 0.1s;
}
.btn:hover  { opacity: 0.88; }
.btn:active { transform: scale(0.97); }
.btn-primary   { background: #4f8ef7; color: #fff; }
.btn-secondary { background: #e0e0e0; color: #333; }
.btn-success   { background: #27ae60; color: #fff; }
.btn-danger    { background: #e74c3c; color: #fff; }
.btn-sm { padding: 4px 12px; font-size: 0.82rem; }

/* ===== Глобальні стилі форми ===== */
.form-group { margin-bottom: 14px; }
.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 4px;
  font-size: 0.9rem;
}
.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1.5px solid #ddd;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: border-color 0.2s;
  font-family: inherit;
}
.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #4f8ef7;
}
.form-group textarea { min-height: 100px; resize: vertical; }
.field-error { color: #e74c3c; font-size: 0.8rem; margin-top: 3px; }

/* ===== Модальне вікно ===== */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
  padding: 16px;
}
.modal {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 620px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 40px rgba(0,0,0,0.2);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px 0;
}
.modal-header h2 { font-size: 1.2rem; }
.modal-close {
  background: none; border: none; font-size: 1.3rem;
  cursor: pointer; color: #888;
}
.modal-close:hover { color: #333; }

/* ===== Lightbox ===== */
.lightbox-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.85);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
  animation: fadeIn 0.2s ease;
}
.lightbox-content {
  position: relative;
  max-width: 90vw; max-height: 90vh;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  overflow: auto;
}
.lightbox-content img { max-width: 100%; border-radius: 8px; }
.lightbox-text {
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 0.9rem;
  max-width: 700px;
}
.lightbox-close {
  position: absolute; top: 8px; right: 12px;
  background: none; border: none; font-size: 1.4rem;
  cursor: pointer; color: #555;
}
.lightbox-close:hover { color: #000; }
@keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }
</style>

<template>
  <div class="app">

    <!-- ===== Шапка сайта ===== -->
    <header class="app-header">
      <h1>💬 SPA Коментарии</h1>
      <p class="subtitle">Оставляйте комментарии и отвечайте другим</p>
    </header>

    <main class="app-main">

      <!-- ===== Панель действий ===== -->
      <div class="actions-bar">
        <button class="btn btn-primary" @click="openForm(null)">
          + Новый комментарий
        </button>
        <span v-if="wsConnected" class="ws-badge ws-online">● Live</span>
        <span v-else class="ws-badge ws-offline">● Offline</span>
      </div>

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

    <div v-if="showForm" class="modal-overlay" @click.self="closeForm">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ formParentId ? 'Ответ на комментарий' : 'Новый комментарий' }}</h2>
          <button class="modal-close" @click="closeForm">✕</button>
        </div>
        <CommentForm
          :parent-id="formParentId"
          @submitted="onCommentSubmitted"
          @cancel="closeForm"
        />
      </div>
    </div>

    <div v-if="lightbox" class="lightbox-overlay" @click="lightbox = null">
      <div class="lightbox-content" @click.stop>
        <button class="lightbox-close" @click="lightbox = null">✕</button>
        <img v-if="lightbox.type === 'image'" :src="lightbox.url" alt="preview" />
        <pre v-else class="lightbox-text">{{ lightbox.content }}</pre>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, provide } from 'vue'

import api from './api/comments.js'
import CommentList from './components/CommentList.vue'
import CommentForm from './components/CommentForm.vue'

// ==================== СОСТОЯНИЕ ====================

const comments     = ref([])
const total        = ref(0)
const currentPage  = ref(1)
const totalPages   = ref(1)
const sortBy       = ref('created_at')
const sortOrder    = ref('desc')
const loading      = ref(false)
const showForm     = ref(false)
const formParentId = ref(null)
const wsConnected  = ref(false)
const lightbox     = ref(null)
const replySubmittedFor = ref(null) // сигнал для CommentList — какой родитель обновить

// Последний комментарий полученный через WebSocket.
// Передаётся дочерним компонентам через provide/inject.
// CommentList следит за этим значением и обновляет раскрытые ответы.
const wsLastComment = ref(null)

// ==================== PROVIDE ====================

// Передаём функцию открытия lightbox всем дочерним компонентам.
// CommentItem вызывает её когда пользователь кликает на файл.
provide('openLightbox', (data) => { lightbox.value = data })

// Передаём последний WS-комментарий вниз по дереву компонентов.
// CommentList подписывается на него через inject и watch,
// чтобы автоматически обновлять раскрытые ответы.
provide('wsLastComment', wsLastComment)
provide('replySubmittedFor', replySubmittedFor)

// ==================== WEBSOCKET ====================

let socket = null

function connectWebSocket() {
  const wsUrl = `ws://${window.location.host}/ws/comments/`
  socket = new WebSocket(wsUrl)

  socket.onopen = () => { wsConnected.value = true }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)

    // Сохраняем последний комментарий — CommentList отреагирует через watch.
    // Это нужно для автообновления раскрытых ответов когда приходит новая
    // реплика (комментарий с parent !== null).
    wsLastComment.value = data.comment

    // Если это новый корневой комментарий (без родителя) —
    // добавляем его в начало списка без перезагрузки страницы.
    if (data.type === 'new_comment' && data.comment.parent === null) {
      if (currentPage.value === 1 && sortOrder.value === 'desc') {
        comments.value.unshift(data.comment)
        total.value += 1
      }
    }
  }

  socket.onclose = () => {
    wsConnected.value = false
    setTimeout(connectWebSocket, 3000)
  }

  socket.onerror = () => { socket.close() }
}

// ==================== ЗАГРУЗКА ДАННЫХ ====================

async function loadComments() {
  loading.value = true
  try {
    const res = await api.getComments({
      page:       currentPage.value,
      sort_by:    sortBy.value,
      sort_order: sortOrder.value,
    })
    comments.value   = res.data.results
    total.value      = res.data.count
    totalPages.value = Math.ceil(res.data.count / 25)
  } catch (err) {
    console.error('Помилка завантаження коментарів:', err)
  } finally {
    loading.value = false
  }
}

// ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

function openForm(parentId) {
  formParentId.value = parentId
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  formParentId.value = null
}

async function onCommentSubmitted() {
  // Сохраняем parentId ДО вызова closeForm() — она сбрасывает formParentId в null.
  // Нам нужен этот ID чтобы сказать CommentList какие ответы перезагрузить.
  const parentId = formParentId.value

  closeForm()
  currentPage.value = 1
  await loadComments()

  // Если был добавлен ОТВЕТ (не корневой комментарий) — сигнализируем CommentList.
  // Используем объект с timestamp: даже если parentId тот же, watch сработает
  // потому что это новый объект (другая ссылка в памяти).
  if (parentId !== null) {
    replySubmittedFor.value = { parentId, ts: Date.now() }
  }
}

function handleSort({ field, order }) {
  sortBy.value      = field
  sortOrder.value   = order
  currentPage.value = 1
  loadComments()
}

function handlePageChange(page) {
  currentPage.value = page
  loadComments()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ==================== ЖИЗНЕННЫЙ ЦИКЛ ====================

onMounted(() => {
  loadComments()
  connectWebSocket()
})

onUnmounted(() => {
  if (socket) socket.close()
})
</script>

<style>
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

.actions-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.ws-badge { font-size: 0.8rem; font-weight: 600; }
.ws-online  { color: #27ae60; }
.ws-offline { color: #e74c3c; }

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

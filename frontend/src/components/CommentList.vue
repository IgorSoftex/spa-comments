<template>
  <div class="comment-list">
    <div v-if="loading" class="loading">Загрузка...</div>

    <div v-else-if="!comments.length" class="empty">
      Комментариев еще нет. Будьте первым! 🚀
    </div>

    <div v-else>
      <div class="table-meta">
        Всего комментариев: <strong>{{ total }}</strong>
      </div>

      <div class="table-wrapper">
        <table class="comments-table">
          <thead>
            <tr>
              <th @click="toggleSort('user_name')" class="sortable">
                User Name {{ sortIcon('user_name') }}
              </th>
              <th @click="toggleSort('email')" class="sortable">
                E-mail {{ sortIcon('email') }}
              </th>
              <th @click="toggleSort('created_at')" class="sortable">
                Дата {{ sortIcon('created_at') }}
              </th>
              <th>Сообщение</th>
              <th>Ответы</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="comment in comments" :key="comment.id">
              <tr class="comment-row">
                <td>
                  <span class="username">{{ comment.user_name }}</span>
                  <a v-if="comment.home_page" :href="comment.home_page" target="_blank" class="homepage-link" title="Домашня сторінка">🔗</a>
                </td>
                <td><a :href="`mailto:${comment.email}`" class="email-link">{{ comment.email }}</a></td>
                <td class="date-cell">{{ formatDate(comment.created_at) }}</td>
                <td class="text-cell" v-html="comment.text"></td>
                <td class="center">
                  <span class="replies-badge" v-if="comment.replies_count > 0">
                    {{ comment.replies_count }}
                  </span>
                  <span v-else class="no-replies">—</span>
                </td>
                <td class="actions-cell">
                  <button class="btn btn-sm btn-secondary" @click="toggleReplies(comment)">
                    {{ expandedIds.has(comment.id) ? 'Свернуть' : 'Ответы' }}
                  </button>
                  <button class="btn btn-sm btn-primary" @click="$emit('reply', comment.id)">
                    Ответить
                  </button>
                </td>
              </tr>

              <tr v-if="comment.image || comment.attachment" class="files-row">
                <td colspan="6">
                  <div class="file-previews">
                    <div v-if="comment.image" class="file-thumb" @click="openImage(comment.image)">
                      <img :src="comment.image" :alt="`Image by ${comment.user_name}`" />
                      <span class="file-label">Переглянути</span>
                    </div>
                    <div v-if="comment.attachment" class="file-thumb file-txt" @click="openTxt(comment.attachment)">
                      📄 <span>{{ fileName(comment.attachment) }}</span>
                    </div>
                  </div>
                </td>
              </tr>

              <tr v-if="expandedIds.has(comment.id)" class="replies-row">
                <td colspan="6">
                  <div v-if="loadingReplies.has(comment.id)" class="replies-loading">
                    Завантаження відповідей...
                  </div>
                  <div v-else-if="repliesMap[comment.id]">
                    <CommentItem
                      v-for="reply in repliesMap[comment.id]"
                      :key="reply.id"
                      :comment="reply"
                      :depth="1"
                      @reply="$emit('reply', $event)"
                    />
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <Pagination
        :current-page="currentPage"
        :total-pages="totalPages"
        @change="$emit('page-change', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, inject, watch } from 'vue'
import api from '../api/comments.js'
import CommentItem from './CommentItem.vue'
import Pagination from './Pagination.vue'

const props = defineProps({
  comments:    { type: Array,   default: () => [] },
  total:       { type: Number,  default: 0 },
  currentPage: { type: Number,  default: 1 },
  totalPages:  { type: Number,  default: 1 },
  sortBy:      { type: String,  default: 'created_at' },
  sortOrder:   { type: String,  default: 'desc' },
  loading:     { type: Boolean, default: false },
})

const emit = defineEmits(['reply', 'sort', 'page-change'])

const openLightbox      = inject('openLightbox')
const wsLastComment     = inject('wsLastComment')
const replySubmittedFor = inject('replySubmittedFor')

const expandedIds    = ref(new Set())
const loadingReplies = ref(new Set())
const repliesMap     = reactive({})

// Карта: ID вложенного комментария → ID корневого комментария.
// Нужна чтобы по ID ответа на ответ найти корневой элемент таблицы.
// Пример: Julia(id=3) ответила на Ihor(id=1) → nestedToRootMap[3] = 1
//         Peter(id=5) ответил на Julia(id=3) → nestedToRootMap[5] = 1
// Когда Peter добавляет ответ на Julia — мы перезагружаем replies Ihor.
const nestedToRootMap = reactive({})

// ==================== ДОПОМІЖНІ ФУНКЦІЇ ====================

// Рекурсивно обходит дерево ответов и заполняет nestedToRootMap.
// replies — массив ответов для корневого комментария rootId.
function buildNestedMap(replies, rootId) {
  for (const reply of replies) {
    nestedToRootMap[reply.id] = rootId
    if (reply.replies && reply.replies.length) {
      buildNestedMap(reply.replies, rootId)
    }
  }
}

// Перезагружает список ответов для корневого комментария rootId.
// Используется и при получении WS-сообщения, и при отправке формы.
function reloadReplies(rootId) {
  loadingReplies.value.add(rootId)
  api.getReplies(rootId)
    .then(res => {
      repliesMap[rootId] = res.data.replies
      // Обновляем карту вложенных ID после получения свежих данных
      buildNestedMap(res.data.replies, rootId)
    })
    .catch(err => console.error('Помилка оновлення відповідей:', err))
    .finally(() => loadingReplies.value.delete(rootId))
}

// Ищет корневой комментарий для parentId и перезагружает его если он развернут.
// parentId может быть:
//   1. ID корневого комментария (прямой ответ на элемент таблицы)
//   2. ID вложенного комментария (ответ на ответ любой глубины)
function reloadForParent(parentId) {
  if (expandedIds.value.has(parentId)) {
    // Прямой ответ на корневой комментарий — перезагружаем его
    reloadReplies(parentId)
  } else if (nestedToRootMap[parentId]) {
    // Вложенный ответ — ищем корневой через карту и перезагружаем его
    const rootId = nestedToRootMap[parentId]
    if (expandedIds.value.has(rootId)) {
      reloadReplies(rootId)
    }
  }
}

// ==================== WATCHES ====================

// Реагируем на новый комментарий через WebSocket (от других пользователей).
watch(wsLastComment, (newComment) => {
  if (newComment && newComment.parent !== null) {
    reloadForParent(newComment.parent)
  }
})

// Реагируем на отправку формы текущим пользователем.
// Это основной механизм обновления — надёжнее WebSocket.
watch(replySubmittedFor, (data) => {
  if (data) {
    reloadForParent(data.parentId)
  }
})

// ==================== СОРТУВАННЯ ====================

function toggleSort(field) {
  let order = 'desc'
  if (props.sortBy === field) {
    order = props.sortOrder === 'desc' ? 'asc' : 'desc'
  }
  emit('sort', { field, order })
}

function sortIcon(field) {
  if (props.sortBy !== field) return '↕'
  return props.sortOrder === 'asc' ? '↑' : '↓'
}

// ==================== ВІДПОВІДІ ====================

async function toggleReplies(comment) {
  if (expandedIds.value.has(comment.id)) {
    expandedIds.value.delete(comment.id)
    return
  }
  expandedIds.value.add(comment.id)
  loadingReplies.value.add(comment.id)
  try {
    const res = await api.getReplies(comment.id)
    repliesMap[comment.id] = res.data.replies
    // Строим карту вложенных ID чтобы потом находить корень для любого потомка
    buildNestedMap(res.data.replies, comment.id)
  } catch (err) {
    console.error('Помилка завантаження відповідей:', err)
  } finally {
    loadingReplies.value.delete(comment.id)
  }
}

// ==================== ФАЙЛИ (LIGHTBOX) ====================

function openImage(url) {
  openLightbox({ type: 'image', url })
}

async function openTxt(url) {
  try {
    const res = await fetch(url)
    const text = await res.text()
    openLightbox({ type: 'text', content: text })
  } catch {
    window.open(url, '_blank')
  }
}

function fileName(url) {
  // decodeURIComponent розкодовує URL-encoded назву файлу:
  // %D0%9E%D1%82%D0%BA... → Откл...
  // try/catch на випадок якщо рядок не можна розкодувати (зламаний URL)
  try {
    return decodeURIComponent(url.split('/').pop())
  } catch {
    return url.split('/').pop()
  }
}

// ==================== ФОРМАТУВАННЯ ДАТИ ====================

function formatDate(dt) {
  return new Date(dt).toLocaleString('uk-UA', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<style scoped>
.loading, .empty {
  text-align: center;
  padding: 48px 0;
  color: #888;
  font-size: 1.1rem;
}

.table-meta {
  margin-bottom: 10px;
  color: #666;
  font-size: 0.9rem;
}

.table-wrapper { overflow-x: auto; }

.comments-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}

.comments-table thead {
  background: #f8f9ff;
  border-bottom: 2px solid #e8eaf0;
}

.comments-table th {
  padding: 12px 14px;
  text-align: left;
  font-size: 0.85rem;
  font-weight: 700;
  color: #555;
  white-space: nowrap;
}

.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: #4f8ef7; }

.comments-table td {
  padding: 12px 14px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
  font-size: 0.9rem;
}

.comment-row:hover td { background: #fafbff; }

.username { font-weight: 600; color: #2d3436; }
.homepage-link { margin-left: 6px; text-decoration: none; }
.email-link { color: #4f8ef7; text-decoration: none; }
.email-link:hover { text-decoration: underline; }

.date-cell { white-space: nowrap; color: #777; font-size: 0.82rem; }
.text-cell { max-width: 300px; }
.center { text-align: center; }

.replies-badge {
  background: #4f8ef7;
  color: #fff;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 0.8rem;
  font-weight: 700;
}
.no-replies { color: #bbb; }

.actions-cell {
  white-space: nowrap;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.files-row td { padding: 4px 14px 12px; }
.file-previews { display: flex; gap: 12px; flex-wrap: wrap; }
.file-thumb {
  cursor: pointer;
  border: 2px solid #e0e7ff;
  border-radius: 8px;
  padding: 4px;
  transition: border-color 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.file-thumb:hover { border-color: #4f8ef7; }
.file-thumb img { max-width: 80px; max-height: 60px; border-radius: 4px; }
.file-label { font-size: 0.75rem; color: #4f8ef7; }
.file-txt { padding: 8px 14px; font-size: 0.85rem; color: #555; }

.replies-row td { padding: 0 0 0 48px; }
.replies-loading { padding: 12px; color: #888; }
</style>

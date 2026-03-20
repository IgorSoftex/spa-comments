<template>
  <div class="comment-item" :class="{ 'is-reply': depth > 0 }">

    <!-- Шапка комментария: имя, email, дата -->
    <div class="comment-header">
      <div class="comment-author">
        <!-- Если есть домашняя страница — имя кликабельно -->

        <a v-if="comment.home_page" :href="comment.home_page" target="_blank" class="author-name">{{ comment.user_name }}</a>
        <span v-else class="author-name">{{ comment.user_name }}</span>

        <span class="author-email">{{ comment.email }}</span>
      </div>

      <!-- Дата создания комментария -->
      <!-- formatDate() преобразует ISO строку в читаемый формат -->
      <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
    </div>

    <!-- Текст комментария -->
    <!-- v-html — отображает HTML-теги внутри текста.
         Это безопасно: Django уже очистил текст через bleach,
         оставив только разрешённые теги: a, strong, i, code -->
    <div class="comment-text" v-html="comment.text"></div>

    <!-- Изображение (если прикреплено) -->
    <div v-if="comment.image" class="comment-image">
      <img :src="comment.image" alt="Прикреплённое изображение" />
    </div>

    <!-- Файл-вложение (если прикреплено) -->
    <div v-if="comment.attachment" class="comment-attachment">
      <a :href="comment.attachment" target="_blank">
        📎 Скачать вложение
      </a>
    </div>

    <!-- Кнопка "Ответить" и счётчик ответов -->
    <div class="comment-footer">
      <button @click="toggleReplyForm" class="btn-reply">
        💬 Ответить
      </button>
      <span v-if="comment.replies_count > 0" class="replies-count">
        {{ comment.replies_count }}
        {{ pluralize(comment.replies_count, 'ответ', 'ответа', 'ответов') }}
      </span>
    </div>

    <!-- Форма ответа на этот комментарий -->
    <!-- v-if="showReplyForm" — показывается только после нажатия "Ответить" -->
    <div v-if="showReplyForm" class="reply-form">
      <h4>Ответить на комментарий {{ comment.user_name }}</h4>

      <div v-if="replyError" class="alert alert-error">{{ replyError }}</div>
      <div v-if="replySuccess" class="alert alert-success">{{ replySuccess }}</div>

      <div class="form-group">
        <input v-model="replyForm.user_name" placeholder="Имя *" required />
      </div>
      <div class="form-group">
        <input v-model="replyForm.email" type="email" placeholder="Email *" required />
      </div>
      <div class="form-group">
        <textarea v-model="replyForm.text" rows="3" placeholder="Текст ответа *" required></textarea>
      </div>

      <!-- Мини-капча для ответа -->
      <div class="form-group captcha-group">
        <div class="captcha-row">
          <img :src="replyCaptchaUrl" alt="CAPTCHA" class="captcha-image" />
          <button type="button" @click="refreshReplyCaptcha" class="btn-refresh">
            🔄
          </button>
        </div>
        <input v-model="replyForm.captcha" placeholder="Текст с картинки *" />
      </div>

      <div class="reply-buttons">
        <button @click="submitReply" :disabled="replySubmitting" class="btn-submit">
          {{ replySubmitting ? 'Отправка...' : 'Отправить ответ' }}
        </button>
        <button @click="toggleReplyForm" class="btn-cancel">Отмена</button>
      </div>
    </div>

    <!-- Вложенные ответы (replies) -->
    <!-- Рекурсия: CommentItem отображает CommentItem для каждого ответа.
         :depth="depth + 1" — увеличиваем глубину вложенности для отступов. -->
    <div v-if="replies.length > 0" class="replies">
      <CommentItem
        v-for="reply in replies"
        :key="reply.id"
        :comment="reply"
        :depth="depth + 1"
      />
    </div>

    <!-- Кнопка загрузки ответов (если они есть но ещё не загружены) -->
    <button
      v-if="comment.replies_count > 0 && !repliesLoaded && depth === 0"
      @click="loadReplies"
      class="btn-load-replies"
    >
      Показать ответы ({{ comment.replies_count }})
    </button>

  </div>
</template>

<script setup>
import { ref, defineProps } from 'vue'
import axios from 'axios'
import { useCommentsStore } from '../stores/comments'

// defineProps — объявляем входные параметры компонента.
// comment — объект комментария переданный из CommentList или родительского CommentItem.
// depth — глубина вложенности (0 = корневой, 1 = ответ, 2 = ответ на ответ...)
const props = defineProps({
  comment: { type: Object, required: true },
  depth:   { type: Number, default: 0 },
})

const store = useCommentsStore()

// Список загруженных ответов на этот комментарий
const replies = ref([])

// Флаг — были ли уже загружены ответы
const repliesLoaded = ref(false)

// Показывать ли форму ответа
const showReplyForm = ref(false)

// Данные формы ответа
const replyForm = ref({
  user_name: '',
  email: '',
  text: '',
  captcha: '',
})

const replySubmitting = ref(false)
const replyError = ref('')
const replySuccess = ref('')

// URL капчи для формы ответа (отдельная от основной формы)
const replyCaptchaUrl = ref(`/api/captcha/?t=${Date.now()}`)

// Переключает видимость формы ответа
function toggleReplyForm() {
  showReplyForm.value = !showReplyForm.value
  if (showReplyForm.value) {
    refreshReplyCaptcha()
  }
}

// Обновляет капчу для формы ответа
function refreshReplyCaptcha() {
  replyCaptchaUrl.value = `/api/captcha/?t=${Date.now()}`
}

// Загружает ответы на этот комментарий с сервера.
// GET /api/comments/<id>/ возвращает комментарий с вложенными replies.
async function loadReplies() {
  try {
    const response = await axios.get(`/api/comments/${props.comment.id}/`)
    replies.value = response.data.replies || []
    repliesLoaded.value = true
  } catch (err) {
    console.error('Ошибка загрузки ответов:', err)
  }
}

// Отправляет ответ на комментарий
async function submitReply() {
  replySubmitting.value = true
  replyError.value = ''
  replySuccess.value = ''

  // Проверяем капчу
  const captchaValid = await store.verifyCaptcha(replyForm.value.captcha)
  if (!captchaValid) {
    replyError.value = 'Неверная капча.'
    refreshReplyCaptcha()
    replyForm.value.captcha = ''
    replySubmitting.value = false
    return
  }

  // Формируем данные ответа.
  // parent — id родительского комментария (на который отвечаем)
  const formData = new FormData()
  formData.append('user_name', replyForm.value.user_name)
  formData.append('email', replyForm.value.email)
  formData.append('text', replyForm.value.text)
  formData.append('parent', props.comment.id)

  const success = await store.createComment(formData)

  if (success) {
    replySuccess.value = 'Ответ добавлен!'
    replyForm.value = { user_name: '', email: '', text: '', captcha: '' }
    // Перезагружаем ответы чтобы показать новый
    await loadReplies()
    setTimeout(() => { showReplyForm.value = false }, 1500)
  } else {
    replyError.value = 'Ошибка при отправке ответа.'
  }

  replySubmitting.value = false
}

// Форматирует ISO дату в читаемый формат: "20.03.2026 15:30"
function formatDate(isoString) {
  const date = new Date(isoString)
  return date.toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

// Склонение числительных для русского языка.
// pluralize(1, 'ответ', 'ответа', 'ответов') → '1 ответ'
// pluralize(3, 'ответ', 'ответа', 'ответов') → '3 ответа'
// pluralize(11, 'ответ', 'ответа', 'ответов') → '11 ответов'
function pluralize(count, one, few, many) {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod10 === 1 && mod100 !== 11) return `${count} ${one}`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return `${count} ${few}`
  return `${count} ${many}`
}
</script>

<style scoped>
.comment-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 15px;
  background: #fff;
}

/* Вложенные комментарии имеют отступ и другой фон */
.comment-item.is-reply {
  margin-left: 20px;
  background: #f9f9f9;
  border-left: 3px solid #2c3e50;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.comment-author { display: flex; flex-direction: column; gap: 2px; }

.author-name {
  font-weight: bold;
  color: #2c3e50;
  text-decoration: none;
  font-size: 15px;
}

.author-name:hover { text-decoration: underline; }

.author-email { font-size: 12px; color: #999; }

.comment-date { font-size: 12px; color: #aaa; white-space: nowrap; }

.comment-text {
  margin-bottom: 10px;
  line-height: 1.6;
  font-size: 14px;
}

.comment-image img {
  max-width: 100%;
  max-height: 240px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.comment-attachment { margin-bottom: 10px; font-size: 13px; }
.comment-attachment a { color: #2980b9; text-decoration: none; }

.comment-footer {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 10px;
}

.btn-reply {
  padding: 4px 12px;
  border: 1px solid #2c3e50;
  border-radius: 4px;
  background: transparent;
  color: #2c3e50;
  cursor: pointer;
  font-size: 13px;
}

.replies-count { font-size: 13px; color: #999; }

.replies { margin-top: 15px; }

.btn-load-replies {
  margin-top: 10px;
  padding: 6px 14px;
  border: 1px dashed #aaa;
  border-radius: 4px;
  background: transparent;
  color: #666;
  cursor: pointer;
  font-size: 13px;
  width: 100%;
}

.reply-form {
  margin-top: 15px;
  padding: 15px;
  background: #f0f4f8;
  border-radius: 6px;
}

.reply-form h4 { margin-bottom: 12px; font-size: 14px; color: #555; }

.form-group { margin-bottom: 10px; }

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.captcha-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.captcha-image { border: 1px solid #ddd; border-radius: 4px; }

.btn-refresh {
  padding: 4px 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  background: #fff;
}

.reply-buttons { display: flex; gap: 10px; margin-top: 10px; }

.btn-submit {
  padding: 8px 16px;
  background: #2c3e50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.btn-submit:disabled { background: #aaa; cursor: not-allowed; }

.btn-cancel {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.alert {
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 10px;
  font-size: 13px;
}

.alert-success { background: #d4edda; color: #155724; }
.alert-error   { background: #f8d7da; color: #721c24; }
</style>

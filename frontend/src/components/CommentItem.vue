<template>
  <!-- Рекурсивний компонент для каскадного відображення відповідей -->
  <div class="comment-item" :style="{ marginLeft: depth * 24 + 'px' }">
    <div class="comment-bubble">
      <div class="comment-meta">
        <span class="ci-username">{{ comment.user_name }}</span>
        <a v-if="comment.home_page" :href="comment.home_page" target="_blank" class="ci-homepage">🔗</a>
        <span class="ci-email">{{ comment.email }}</span>
        <span class="ci-date">{{ formatDate(comment.created_at) }}</span>
      </div>

      <div class="comment-text" v-html="comment.text"></div>

      <!-- Вкладені файли -->
      <div v-if="comment.image || comment.attachment" class="ci-files">
        <div v-if="comment.image" class="ci-thumb" @click="openImage(comment.image)">
          <img :src="comment.image" alt="attachment" />
        </div>
        <div v-if="comment.attachment" class="ci-txt" @click="openTxt(comment.attachment)">
          📄 {{ fileName(comment.attachment) }}
        </div>
      </div>

      <div class="ci-actions">
        <button class="btn btn-sm btn-primary" @click="$emit('reply', comment.id)">
          Відповісти
        </button>
        <button
          v-if="comment.replies && comment.replies.length"
          class="btn btn-sm btn-secondary"
          @click="showReplies = !showReplies"
        >
          {{ showReplies ? 'Згорнути' : `Відповіді (${comment.replies.length})` }}
        </button>
      </div>
    </div>

    <!-- Рекурсивні відповіді -->
    <div v-if="showReplies && comment.replies && comment.replies.length" class="ci-replies">
      <CommentItem
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :depth="depth + 1"
        @reply="$emit('reply', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'

const props = defineProps({
  comment: { type: Object, required: true },
  depth:   { type: Number, default: 0 },
})

defineEmits(['reply'])

const showReplies = ref(true)
const openLightbox = inject('openLightbox')

function formatDate(dt) {
  return new Date(dt).toLocaleString('uk-UA', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

function openImage(url) { openLightbox({ type: 'image', url }) }

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
  try {
    return decodeURIComponent(url.split('/').pop())
  } catch {
    return url.split('/').pop()
  }
}

</script>

<style scoped>
.comment-item { margin-bottom: 10px; }

.comment-bubble {
  background: #f8f9ff;
  border: 1px solid #e0e7ff;
  border-left: 3px solid #4f8ef7;
  border-radius: 8px;
  padding: 12px 16px;
}

.comment-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ci-username { font-weight: 700; color: #2d3436; }
.ci-homepage { text-decoration: none; }
.ci-email    { color: #4f8ef7; font-size: 0.85rem; }
.ci-date     { color: #aaa; font-size: 0.8rem; margin-left: auto; }

.comment-text { font-size: 0.9rem; line-height: 1.5; margin-bottom: 8px; }
/* Безпечний рендер HTML — bleach вже очистив на сервері */
.comment-text :deep(a)      { color: #4f8ef7; }
.comment-text :deep(code)   { background: #eee; padding: 1px 5px; border-radius: 4px; font-size: 0.85em; }
.comment-text :deep(strong) { font-weight: 700; }
.comment-text :deep(i)      { font-style: italic; }

.ci-files {
  display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 8px;
}
.ci-thumb {
  cursor: pointer;
  border: 2px solid #e0e7ff;
  border-radius: 6px;
  padding: 3px;
  transition: border-color 0.2s;
}
.ci-thumb:hover { border-color: #4f8ef7; }
.ci-thumb img { max-width: 80px; max-height: 60px; border-radius: 4px; display: block; }
.ci-txt {
  cursor: pointer;
  color: #4f8ef7;
  font-size: 0.85rem;
  padding: 4px 8px;
  border: 1.5px dashed #b0c4ff;
  border-radius: 6px;
}
.ci-txt:hover { background: #eef2ff; }

.ci-actions { display: flex; gap: 6px; margin-top: 6px; }
.ci-replies { margin-top: 8px; }
</style>

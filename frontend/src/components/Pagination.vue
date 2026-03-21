<template>
  <div v-if="totalPages > 1" class="pagination">
    <button
      class="page-btn"
      :disabled="currentPage === 1"
      @click="$emit('change', 1)"
    >«</button>

    <button
      class="page-btn"
      :disabled="currentPage === 1"
      @click="$emit('change', currentPage - 1)"
    >‹</button>

    <template v-for="page in visiblePages" :key="page">
      <span v-if="page === '...'" class="page-ellipsis">...</span>
      <button
        v-else
        class="page-btn"
        :class="{ active: page === currentPage }"
        @click="$emit('change', page)"
      >{{ page }}</button>
    </template>

    <button
      class="page-btn"
      :disabled="currentPage === totalPages"
      @click="$emit('change', currentPage + 1)"
    >›</button>

    <button
      class="page-btn"
      :disabled="currentPage === totalPages"
      @click="$emit('change', totalPages)"
    >»</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalPages:  { type: Number, required: true },
})

defineEmits(['change'])

/**
 * Формуємо список сторінок зі «...» для великої кількості сторінок.
 */
const visiblePages = computed(() => {
  const pages = []
  const { currentPage: cp, totalPages: tp } = props

  if (tp <= 7) {
    for (let i = 1; i <= tp; i++) pages.push(i)
    return pages
  }

  pages.push(1)
  if (cp > 3) pages.push('...')
  for (let i = Math.max(2, cp - 1); i <= Math.min(tp - 1, cp + 1); i++) {
    pages.push(i)
  }
  if (cp < tp - 2) pages.push('...')
  pages.push(tp)

  return pages
})
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  margin-top: 24px;
  flex-wrap: wrap;
}

.page-btn {
  min-width: 36px;
  height: 36px;
  border: 1.5px solid #dde3f5;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  color: #444;
  transition: background 0.15s, border-color 0.15s;
}
.page-btn:hover:not(:disabled) {
  background: #eef2ff;
  border-color: #4f8ef7;
  color: #4f8ef7;
}
.page-btn.active {
  background: #4f8ef7;
  border-color: #4f8ef7;
  color: #fff;
}
.page-btn:disabled { opacity: 0.4; cursor: default; }
.page-ellipsis { color: #aaa; padding: 0 4px; }
</style>

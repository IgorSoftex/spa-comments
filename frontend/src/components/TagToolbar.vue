<template>
  <!--
    Панель кнопок для вставки HTML-тегів у textarea.
    Вимога ТЗ: кнопки [i], [strong], [code], [a]
  -->
  <div class="tag-toolbar">
    <span class="toolbar-label">Теги:</span>
    <button
      v-for="tag in tags"
      :key="tag.label"
      class="tag-btn"
      type="button"
      :title="tag.title"
      @click="insertTag(tag)"
    >
      {{ tag.label }}
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  /** ref на textarea, у який вставляємо теги */
  textareaRef: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue'])

const tags = [
  { label: '[i]',      open: '<i>',      close: '</i>',      title: 'Курсив' },
  { label: '[strong]', open: '<strong>',  close: '</strong>',  title: 'Жирний' },
  { label: '[code]',   open: '<code>',    close: '</code>',    title: 'Код' },
  { label: '[a]',      open: '<a href="" title="">', close: '</a>', title: 'Посилання' },
]

function insertTag(tag) {
  const el = props.textareaRef
  if (!el) return

  const start = el.selectionStart
  const end   = el.selectionEnd
  const selected = el.value.slice(start, end)
  const before    = el.value.slice(0, start)
  const after     = el.value.slice(end)

  const insertion = `${tag.open}${selected}${tag.close}`
  const newValue  = before + insertion + after

  // Оновлюємо значення textarea
  el.value = newValue
  emit('update:modelValue', newValue)

  // Встановлюємо курсор після відкриваючого тегу
  const cursorPos = start + tag.open.length + selected.length + tag.close.length
  el.focus()
  el.setSelectionRange(cursorPos, cursorPos)
}
</script>

<style scoped>
.tag-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.toolbar-label {
  font-size: 0.82rem;
  color: #888;
  font-weight: 600;
}
.tag-btn {
  padding: 3px 10px;
  border: 1.5px solid #d0d8f0;
  border-radius: 6px;
  background: #f0f4ff;
  color: #4f6ef7;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.tag-btn:hover {
  background: #dce6ff;
  border-color: #4f8ef7;
}
</style>

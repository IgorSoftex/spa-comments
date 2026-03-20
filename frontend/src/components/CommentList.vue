<template>
  <div class="comment-list">

    <div class="list-header">
      <h2>Комментарии</h2>

      <!-- Панель сортировки -->
      <!-- Пользователь может выбрать по какому полю сортировать -->
      <div class="sorting">
        <span>Сортировка:</span>

        <!-- Кнопка активна (class active) если текущая сортировка совпадает -->
        <button
          :class="{ active: store.ordering === '-created_at' }"
          @click="store.setOrdering('-created_at')"
        >
          Новые ↓
        </button>

        <button
          :class="{ active: store.ordering === 'created_at' }"
          @click="store.setOrdering('created_at')"
        >
          Старые ↑
        </button>

        <button
          :class="{ active: store.ordering === 'user_name' }"
          @click="store.setOrdering('user_name')"
        >
          Имя А-Я
        </button>

        <button
          :class="{ active: store.ordering === 'email' }"
          @click="store.setOrdering('email')"
        >
          Email А-Я
        </button>
      </div>
    </div>

    <!-- Индикатор загрузки — показывается пока store.loading = true -->
    <div v-if="store.loading" class="loading">
      Загрузка комментариев...
    </div>

    <!-- Сообщение об ошибке — показывается если store.error не null -->
    <div v-else-if="store.error" class="error">
      {{ store.error }}
    </div>

    <!-- Сообщение если комментариев нет -->
    <div v-else-if="store.comments.length === 0" class="empty">
      Комментариев пока нет. Будьте первым!
    </div>

    <!-- Список комментариев -->
    <!-- v-else — показывается если нет загрузки, ошибок и список не пустой -->
    <div v-else>
      <!--
        v-for — директива для перебора массива и отображения каждого элемента.
        :key — уникальный идентификатор для каждого элемента.
        Vue использует key для эффективного обновления DOM —
        при изменении данных обновляет только изменившиеся элементы.
      -->
      <CommentItem
        v-for="comment in store.comments"
        :key="comment.id"
        :comment="comment"
      />
    </div>

  </div>
</template>

<script setup>
// onMounted — хук жизненного цикла Vue.
// Функция внутри onMounted() вызывается когда компонент
// добавлен в DOM и готов к работе.
import { onMounted } from 'vue'
import { useCommentsStore } from '../stores/comments'
import CommentItem from './CommentItem.vue'

const store = useCommentsStore()

// При монтировании компонента:
// 1. Загружаем список комментариев с сервера
// 2. Подключаемся к WebSocket для обновлений в реальном времени
onMounted(() => {
  store.fetchComments()
  store.connectWebSocket()
})
</script>

<style scoped>
.comment-list {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

h2 { color: #2c3e50; }

.sorting {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #666;
}

.sorting button {
  padding: 5px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  background: #f9f9f9;
  font-size: 13px;
  transition: all 0.2s;
}

/* Активная кнопка сортировки выделяется цветом */
.sorting button.active {
  background-color: #2c3e50;
  color: white;
  border-color: #2c3e50;
}

.loading, .empty {
  text-align: center;
  padding: 30px;
  color: #999;
  font-size: 15px;
}

.error {
  text-align: center;
  padding: 20px;
  color: #e74c3c;
  background: #fdf0f0;
  border-radius: 4px;
}
</style>

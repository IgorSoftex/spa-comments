<!--
  App.vue — корневой компонент приложения.
  Это "скелет" страницы: шапка, основной контент, подвал.
  Все остальные компоненты (CommentForm, CommentList) вкладываются сюда.

  Структура однофайлового компонента Vue (.vue файл):
    <template> — HTML-разметка компонента
    <script>   — JavaScript логика
    <style>    — CSS стили (scoped — применяются только к этому компоненту)
-->
<template>
  <div id="app-wrapper">

    <!-- Шапка сайта -->
    <header class="header">
      <h1>💬 SPA Comments</h1>
      <p>Система комментариев в реальном времени</p>
    </header>

    <!-- Основной контент -->
    <main class="main-content">

      <!-- Форма добавления нового комментария -->
      <!-- CommentForm — наш компонент из src/components/CommentForm.vue -->
      <CommentForm />

      <!-- Список всех комментариев -->
      <!-- CommentList — наш компонент из src/components/CommentList.vue -->
      <CommentList />

    </main>

    <!-- Подвал сайта -->
    <footer class="footer">
      <p>SPA Comments © 2024</p>
    </footer>

  </div>
</template>

<script setup>
// Composition API с <script setup> — современный способ написания компонентов Vue 3.
// Всё что объявлено здесь автоматически доступно в <template>.

// Импортируем дочерние компоненты.
// Vue автоматически регистрирует их при импорте в <script setup>.
import CommentForm from './components/CommentForm.vue'
import CommentList from './components/CommentList.vue'
</script>

<style>
/* Глобальные стили — применяются ко всей странице */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: Arial, sans-serif;
  background-color: #f5f5f5;
  color: #333;
}

.header {
  background-color: #2c3e50;
  color: white;
  padding: 20px;
  text-align: center;
}

.header p {
  margin-top: 5px;
  font-size: 14px;
  opacity: 0.8;
}

.main-content {
  max-width: 800px;
  margin: 30px auto;
  padding: 0 20px;
}

.footer {
  text-align: center;
  padding: 20px;
  margin-top: 40px;
  color: #999;
  font-size: 13px;
}
</style>

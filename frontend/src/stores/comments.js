// Pinia Store — централизованное хранилище данных приложения.
//
// Проблема без store:
//   CommentForm создаёт комментарий → нужно передать его в CommentList →
//   CommentList передаёт в CommentItem → получается длинная цепочка props.
//
// Решение со store:
//   Все компоненты читают данные из одного места (store) и
//   вызывают actions для изменения данных. Никаких цепочек props.

import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

// defineStore — создаёт хранилище с уникальным именем 'comments'.
// Имя используется для идентификации store в Vue DevTools.
export const useCommentsStore = defineStore('comments', () => {

  // ==================== STATE (данные) ====================
  // ref() — реактивная переменная. При изменении Vue автоматически
  // обновляет все компоненты которые используют эту переменную.

  // Список корневых комментариев загруженных с сервера
  const comments = ref([])

  // Флаг загрузки — true пока ждём ответа от сервера
  const loading = ref(false)

  // Текст ошибки — null если ошибок нет
  const error = ref(null)

  // Текущий порядок сортировки комментариев.
  // '-created_at' — сначала новые (минус означает обратный порядок)
  const ordering = ref('-created_at')

  // URL картинки капчи — обновляется при каждом запросе новой капчи
  const captchaUrl = ref('/api/captcha/')

  // ==================== ACTIONS (методы) ====================

  // Загружает список корневых комментариев с сервера.
  // Вызывается при загрузке страницы и после создания нового комментария.
  async function fetchComments() {
    loading.value = true
    error.value = null
    try {
      // GET /api/comments/?ordering=-created_at
      const response = await axios.get('/api/comments/', {
        params: { ordering: ordering.value }
      })
      // Django REST Framework возвращает либо массив либо объект с пагинацией.
      // Проверяем оба варианта.
      comments.value = response.data.results ?? response.data
    } catch (err) {
      error.value = 'Ошибка загрузки комментариев.'
      console.error(err)
    } finally {
      // finally выполняется всегда — и при успехе и при ошибке
      loading.value = false
    }
  }

  // Создаёт новый комментарий.
  // formData — объект FormData с полями: user_name, email, text, image, attachment
  // Возвращает true при успехе или false при ошибке.
  async function createComment(formData) {
    try {
      // POST /api/comments/ с данными формы
      // FormData используется вместо JSON потому что форма может содержать файлы
      await axios.post('/api/comments/', formData, {
        headers: {
          // multipart/form-data — формат для отправки файлов
          'Content-Type': 'multipart/form-data'
        }
      })
      // После создания перезагружаем список комментариев
      await fetchComments()
      return true
    } catch (err) {
      console.error(err)
      return false
    }
  }

  // Обновляет порядок сортировки и перезагружает комментарии.
  // newOrdering — строка: 'created_at', '-created_at', 'user_name', 'email'
  async function setOrdering(newOrdering) {
    ordering.value = newOrdering
    await fetchComments()
  }

  // Обновляет URL капчи добавляя случайный параметр.
  // Браузер кэширует изображения по URL — если URL не меняется,
  // браузер покажет старую картинку. Добавляем ?t=123456 чтобы
  // принудительно загрузить новую картинку с сервера.
  function refreshCaptcha() {
    captchaUrl.value = `/api/captcha/?t=${Date.now()}`
  }

  // Проверяет текст введённый пользователем с картинки капчи.
  // captchaValue — строка которую ввёл пользователь
  // Возвращает true если капча верна, false если нет.
  async function verifyCaptcha(captchaValue) {
    try {
      // POST /api/captcha/verify/ с текстом капчи
      await axios.post('/api/captcha/verify/', { captcha: captchaValue })
      return true
    } catch {
      return false
    }
  }

  // Подключается к WebSocket для получения новых комментариев в реальном времени.
  // Когда другой пользователь создаёт комментарий — мы сразу его получаем
  // без перезагрузки страницы.
  function connectWebSocket() {
    // Определяем протокол: если страница открыта по https — используем wss,
    // иначе ws (ws — незашифрованный, wss — зашифрованный WebSocket)
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/comments/`)

    // Вызывается когда соединение установлено
    ws.onopen = () => {
      console.log('WebSocket подключён')
    }

    // Вызывается когда получено сообщение от сервера
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      // Если сервер сообщает о новом комментарии — перезагружаем список
      if (data.type === 'new_comment') {
        fetchComments()
      }
    }

    // Вызывается при ошибке соединения
    ws.onerror = (err) => {
      console.error('WebSocket ошибка:', err)
    }

    // Вызывается когда соединение закрыто.
    // Пробуем переподключиться через 3 секунды.
    ws.onclose = () => {
      console.log('WebSocket закрыт, переподключение через 3 сек...')
      setTimeout(connectWebSocket, 3000)
    }
  }

  // Возвращаем все переменные и методы которые будут доступны
  // компонентам через useCommentsStore()
  return {
    comments,
    loading,
    error,
    ordering,
    captchaUrl,
    fetchComments,
    createComment,
    setOrdering,
    refreshCaptcha,
    verifyCaptcha,
    connectWebSocket,
  }
})

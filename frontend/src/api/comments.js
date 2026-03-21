/**
 * API-модуль — централизованное место для всех HTTP-запросов к бекенду.
 *
 * Зачем отдельный модуль?
 * Если завтра изменится URL или формат данных, мы правим только этот файл,
 * а не ищем axios.get() по всему проекту.
 *
 * withCredentials: true — разрешает браузеру отправлять cookies вместе
 * с запросами к другому домену/порту. Это нужно для сессий:
 * Django хранит текст CAPTCHA в сессии, а сессия идентифицируется по cookie.
 */
import axios from 'axios'

// Создаём экземпляр axios с базовыми настройками.
// baseURL: '/api' — все запросы будут начинаться с /api.
// Например: api.get('/comments/') → GET /api/comments/
const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // передаём cookies для работы сессий (CAPTCHA)
})

export default {

  /**
   * Получить список корневых комментариев с пагинацией и сортировкой.
   *
   * @param {Object} params - параметры запроса:
   *   page       — номер страницы (по умолчанию 1)
   *   sort_by    — поле сортировки: 'created_at', 'user_name', 'email'
   *   sort_order — направление: 'desc' (новые первые) или 'asc' (старые первые)
   *
   * Ответ сервера: { count, next, previous, results: [...] }
   *   count    — общее количество комментариев
   *   next     — URL следующей страницы или null
   *   previous — URL предыдущей страницы или null
   *   results  — массив комментариев текущей страницы
   */
  getComments(params = {}) {
    return api.get('/comments/', { params })
  },

  /**
   * Получить один комментарий вместе со всеми вложенными ответами (рекурсивно).
   * Вызывается когда пользователь нажимает кнопку "Відповіді" в таблице.
   *
   * @param {number} id — ID комментария
   * Ответ: { id, user_name, text, ..., replies: [ { id, ..., replies: [...] } ] }
   */
  getReplies(id) {
    return api.get(`/comments/${id}/replies/`)
  },

  /**
   * Создать новый комментарий (или ответ на комментарий).
   *
   * @param {FormData} formData — данные формы в формате multipart/form-data.
   * Используем FormData вместо JSON потому что форма может содержать файлы
   * (изображение, текстовый файл). JSON не поддерживает передачу файлов.
   *
   * Поля formData: user_name, email, text, [home_page], [parent], [image], [attachment]
   */
  createComment(formData) {
    return api.post('/comments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /**
   * Получить изображение CAPTCHA в формате base64.
   *
   * Ответ: { image: "data:image/png;base64,iVBORw0KGgo..." }
   * Браузер может отображать base64 напрямую: <img :src="image" />
   * Это удобнее чем отдельный PNG-файл — не нужен дополнительный HTTP-запрос.
   *
   * Одновременно Django сохраняет текст CAPTCHA в сессии пользователя
   * для последующей проверки.
   */
  getCaptcha() {
    return api.get('/captcha/')
  },
}

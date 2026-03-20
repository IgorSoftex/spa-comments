<template>
  <div class="comment-form">
    <h2>Добавить комментарий</h2>

    <!-- Сообщение об успехе -->
    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>

    <!-- Сообщение об ошибке -->
    <div v-if="errorMessage" class="alert alert-error">
      {{ errorMessage }}
    </div>

    <form @submit.prevent="handleSubmit">

      <!-- Имя пользователя -->
      <div class="form-group">
        <label>Имя пользователя *</label>
        <input
          v-model="form.user_name"
          type="text"
          placeholder="Только латиница, цифры и дефис"
          required
        />
      </div>

      <!-- Email -->
      <div class="form-group">
        <label>Email *</label>
        <input
          v-model="form.email"
          type="email"
          placeholder="user@example.com"
          required
        />
      </div>

      <!-- Домашняя страница (необязательно) -->
      <div class="form-group">
        <label>Домашняя страница</label>
        <input
          v-model="form.home_page"
          type="url"
          placeholder="https://example.com"
        />
      </div>

      <!-- Текст комментария -->
      <div class="form-group">
        <label>Комментарий *</label>
        <!-- Панель с разрешёнными тегами -->
        <div class="tags-toolbar">
          <span>Разрешённые теги:</span>
          <button type="button" @click="insertTag('strong')"><strong>B</strong></button>
          <button type="button" @click="insertTag('i')"><i>I</i></button>
          <button type="button" @click="insertTag('code')">code</button>
          <button type="button" @click="insertTag('a')">[a]</button>
        </div>
        <textarea
          ref="textareaRef"
          v-model="form.text"
          rows="5"
          placeholder="Текст комментария..."
          required
        ></textarea>
      </div>

      <!-- Изображение (необязательно) -->
      <div class="form-group">
        <label>Изображение (JPEG/PNG, до 1 МБ)</label>
        <input
          type="file"
          accept="image/jpeg,image/png"
          @change="handleImageChange"
        />
      </div>

      <!-- Вложение (необязательно) -->
      <div class="form-group">
        <label>Файл (TXT/XML, до 100 КБ)</label>
        <input
          type="file"
          accept=".txt,.xml"
          @change="handleAttachmentChange"
        />
      </div>

      <!-- CAPTCHA -->
      <div class="form-group captcha-group">
        <label>Введите текст с картинки *</label>
        <div class="captcha-row">
          <!-- Картинка капчи — src берётся из store -->
          <img
            :src="store.captchaUrl"
            alt="CAPTCHA"
            class="captcha-image"
          />
          <!-- Кнопка обновить капчу -->
          <button type="button" @click="store.refreshCaptcha()" class="btn-refresh">
            🔄 Обновить
          </button>
        </div>
        <input
          v-model="form.captcha"
          type="text"
          placeholder="Введите символы с картинки"
          required
        />
      </div>

      <!-- Кнопка отправки -->
      <button type="submit" class="btn-submit" :disabled="submitting">
        {{ submitting ? 'Отправка...' : 'Отправить комментарий' }}
      </button>

    </form>
  </div>
</template>

<script setup>
// ref() — реактивная переменная (при изменении Vue обновляет шаблон)
import { ref } from 'vue'
// Импортируем наш Pinia store для работы с комментариями
import { useCommentsStore } from '../stores/comments'

// Получаем экземпляр store
const store = useCommentsStore()

// Ссылка на DOM-элемент <textarea> для вставки тегов
const textareaRef = ref(null)

// Флаг — идёт ли отправка формы (чтобы заблокировать кнопку)
const submitting = ref(false)

// Сообщения для пользователя
const successMessage = ref('')
const errorMessage = ref('')

// Данные формы — реактивный объект
// v-model в шаблоне связывает поля ввода с этими значениями
const form = ref({
  user_name: '',
  email: '',
  home_page: '',
  text: '',
  captcha: '',
  image: null,       // File объект или null
  attachment: null,  // File объект или null
})

// Вставляет HTML-тег в позицию курсора в textarea.
// tagName — имя тега: 'strong', 'i', 'code', 'a'
function insertTag(tagName) {
  const textarea = textareaRef.value
  if (!textarea) return

  // Получаем позицию курсора в textarea
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selected = form.value.text.substring(start, end)

  let insertion
  if (tagName === 'a') {
    // Для ссылки добавляем атрибуты href и title
    insertion = `<a href="" title="">${selected}</a>`
  } else {
    insertion = `<${tagName}>${selected}</${tagName}>`
  }

  // Вставляем тег в текст вокруг выделенного фрагмента
  form.value.text =
    form.value.text.substring(0, start) +
    insertion +
    form.value.text.substring(end)
}

// Обработчик выбора файла изображения.
// event.target.files[0] — первый выбранный файл
function handleImageChange(event) {
  form.value.image = event.target.files[0] || null
}

// Обработчик выбора файла вложения
function handleAttachmentChange(event) {
  form.value.attachment = event.target.files[0] || null
}

// Обработчик отправки формы.
// Вызывается при нажатии кнопки "Отправить" (событие @submit.prevent)
// .prevent — предотвращает стандартную отправку формы (перезагрузку страницы)
async function handleSubmit() {
  submitting.value = true
  errorMessage.value = ''
  successMessage.value = ''

  // Шаг 1: Проверяем капчу через API
  const captchaValid = await store.verifyCaptcha(form.value.captcha)
  if (!captchaValid) {
    errorMessage.value = 'Неверная капча. Попробуйте снова.'
    store.refreshCaptcha()
    form.value.captcha = ''
    submitting.value = false
    return  // Прерываем отправку если капча неверна
  }

  // Шаг 2: Формируем FormData для отправки на сервер.
  // FormData используется вместо JSON потому что форма содержит файлы.
  const formData = new FormData()
  formData.append('user_name', form.value.user_name)
  formData.append('email', form.value.email)
  formData.append('text', form.value.text)

  // Добавляем необязательные поля только если они заполнены
  if (form.value.home_page) formData.append('home_page', form.value.home_page)
  if (form.value.image)     formData.append('image', form.value.image)
  if (form.value.attachment) formData.append('attachment', form.value.attachment)

  // Шаг 3: Отправляем комментарий через store
  const success = await store.createComment(formData)

  if (success) {
    successMessage.value = 'Комментарий успешно добавлен!'
    // Очищаем форму после успешной отправки
    form.value = {
      user_name: '', email: '', home_page: '',
      text: '', captcha: '', image: null, attachment: null,
    }
    store.refreshCaptcha()
  } else {
    errorMessage.value = 'Ошибка при отправке. Проверьте данные.'
  }

  submitting.value = false
}
</script>

<style scoped>
/* scoped — стили применяются только к этому компоненту */
.comment-form {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

h2 { margin-bottom: 20px; color: #2c3e50; }

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  font-size: 14px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.tags-toolbar {
  margin-bottom: 5px;
  font-size: 13px;
  color: #666;
}

.tags-toolbar button {
  margin-left: 5px;
  padding: 2px 8px;
  border: 1px solid #ccc;
  border-radius: 3px;
  cursor: pointer;
  background: #f9f9f9;
}

.captcha-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.captcha-image {
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn-refresh {
  padding: 5px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  background: #f9f9f9;
}

.btn-submit {
  width: 100%;
  padding: 12px;
  background-color: #2c3e50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.btn-submit:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

.alert {
  padding: 10px 15px;
  border-radius: 4px;
  margin-bottom: 15px;
  font-size: 14px;
}

.alert-success { background: #d4edda; color: #155724; }
.alert-error   { background: #f8d7da; color: #721c24; }
</style>

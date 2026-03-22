<template>
  <div class="comment-form">
    <!-- Перемикач: Форма / Прев'ю -->
    <div class="form-tabs">
      <button
        :class="['tab-btn', { active: tab === 'form' }]"
        type="button"
        @click="tab = 'form'"
      >Форма</button>
      <button
        :class="['tab-btn', { active: tab === 'preview' }]"
        type="button"
        @click="tab = 'preview'"
      >Прев'ю</button>
    </div>

    <!-- ===== ПРЕВ'Ю ===== -->
    <div v-if="tab === 'preview'" class="preview-pane">
      <div class="preview-bubble">
        <div class="preview-meta">
          <strong>{{ form.user_name || 'Ім\'я' }}</strong>
          <span v-if="form.email" class="preview-email">{{ form.email }}</span>
          <span v-if="form.home_page">
            <a :href="form.home_page" target="_blank">{{ form.home_page }}</a>
          </span>
        </div>
        <div class="preview-text" v-html="previewHtml || '<em>Текст сообщения...</em>'"></div>
      </div>
    </div>

    <!-- ===== ФОРМА ===== -->
    <form v-else @submit.prevent="submitForm" class="form-body">

      <div class="form-row">
        <!-- User Name -->
        <div class="form-group">
          <label for="user_name">User Name <span class="req">*</span></label>
          <input
            id="user_name"
            v-model="form.user_name"
            type="text"
            placeholder="Только латиница и цифры"
            autocomplete="username"
          />
          <div v-if="errors.user_name" class="field-error">{{ errors.user_name }}</div>
        </div>

        <!-- E-mail -->
        <div class="form-group">
          <label for="email">E-mail <span class="req">*</span></label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="example@mail.com"
            autocomplete="email"
          />
          <div v-if="errors.email" class="field-error">{{ errors.email }}</div>
        </div>
      </div>

      <!-- Home page -->
      <div class="form-group">
        <label for="home_page">Home page (необязательно)</label>
        <input
          id="home_page"
          v-model="form.home_page"
          type="url"
          placeholder="https://example.com"
        />
        <div v-if="errors.home_page" class="field-error">{{ errors.home_page }}</div>
      </div>

      <!-- CAPTCHA -->
      <div class="form-group captcha-group">
        <label>CAPTCHA <span class="req">*</span></label>
        <div class="captcha-row">
          <img
            v-if="captchaImage"
            :src="captchaImage"
            class="captcha-img"
            alt="CAPTCHA"
            @click="loadCaptcha"
            title="Натисніть для оновлення"
          />
          <div v-else class="captcha-placeholder" @click="loadCaptcha">
            Завантажити CAPTCHA
          </div>
          <button type="button" class="btn btn-sm btn-secondary captcha-refresh" @click="loadCaptcha">
            ↻
          </button>
        </div>
        <input
          v-model="form.captcha_answer"
          type="text"
          placeholder="Введите символы с картинки"
          style="margin-top: 6px;"
          maxlength="10"
        />
        <div v-if="errors.captcha" class="field-error">{{ errors.captcha }}</div>
      </div>

      <!-- Панель тегів -->
      <div class="form-group">
        <label>Text <span class="req">*</span></label>
        <TagToolbar :textarea-ref="textareaEl" @update:model-value="form.text = $event" />
        <textarea
          ref="textareaEl"
          v-model="form.text"
          placeholder="Ваше сообщение... Можно использовать: <i>, <strong>, <code>, <a>"
          rows="5"
        ></textarea>
        <div v-if="errors.text" class="field-error">{{ errors.text }}</div>
        <div class="text-hint">
          Разрешенные теги: &lt;a href="" title=""&gt;, &lt;code&gt;, &lt;i&gt;, &lt;strong&gt;
        </div>
      </div>

      <!-- Файли -->
      <div class="form-row">
        <!-- Изображение -->
        <div class="form-group">
          <label>Изображение (JPG, GIF, PNG; будет уменьшено до 320×240)</label>
          <input type="file" accept=".jpg,.jpeg,.gif,.png" @change="onImageChange" />
          <div v-if="errors.image" class="field-error">{{ errors.image }}</div>
          <div v-if="imagePreviewUrl" class="img-preview">
            <img :src="imagePreviewUrl" alt="Preview" />
          </div>
        </div>

        <!-- TXT -->
        <div class="form-group">
          <label>Текстовый файл (TXT, макс. 100 КБ)</label>
          <input type="file" accept=".txt" @change="onTxtChange" />
          <div v-if="errors.attachment" class="field-error">{{ errors.attachment }}</div>
          <div v-if="form.attachment" class="file-selected">
            📄 {{ form.attachment.name }}
          </div>
        </div>
      </div>

      <!-- Загальна помилка -->
      <div v-if="errors.general" class="field-error general-error">{{ errors.general }}</div>

      <!-- Кнопки -->
      <div class="form-footer">
        <button type="button" class="btn btn-secondary" @click="$emit('cancel')">
          Отменить
        </button>
        <button type="submit" class="btn btn-success" :disabled="submitting">
          {{ submitting ? 'Отправляем...' : 'Отправить' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api/comments.js'
import TagToolbar from './TagToolbar.vue'

const props = defineProps({
  parentId: { type: Number, default: null },
})
const emit = defineEmits(['submitted', 'cancel'])

const tab         = ref('form')
const submitting  = ref(false)
const captchaImage = ref(null)
const imagePreviewUrl = ref(null)
const textareaEl  = ref(null)

const form = reactive({
  user_name:     '',
  email:         '',
  home_page:     '',
  captcha_answer:'',
  text:          '',
  image:         null,
  attachment:    null,
})

const errors = reactive({})

// --- Прев'ю тексту (без виконання скриптів) ---
const previewHtml = computed(() => {
  // Просте перетворення: показуємо текст як є (bleach очистить на сервері)
  return form.text
})

// --- CAPTCHA ---
async function loadCaptcha() {
  try {
    const res = await api.getCaptcha()
    captchaImage.value = res.data.image
    form.captcha_answer = ''
  } catch (err) {
    console.error('Ошибка загрузки CAPTCHA:', err)
  }
}

// --- Файли ---
function onImageChange(e) {
  const file = e.target.files[0]
  if (!file) return
  form.image = file
  imagePreviewUrl.value = URL.createObjectURL(file)
}

function onTxtChange(e) {
  const file = e.target.files[0]
  if (!file) return
  form.attachment = file
}

// --- Клієнтська валідація ---
function validate() {
  Object.keys(errors).forEach(k => delete errors[k])
  let valid = true

  if (!form.user_name.trim()) {
    errors.user_name = 'User Name является обязательным полем.'
    valid = false
  } else if (!/^[a-zA-Z0-9]+$/.test(form.user_name)) {
    errors.user_name = 'Только латинские буквы и цифры.'
    valid = false
  }

  if (!form.email.trim()) {
    errors.email = 'E-mail является обязательным полем.'
    valid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Неверный формат E-mail.'
    valid = false
  }

  if (form.home_page && !/^https?:\/\/.+/.test(form.home_page)) {
    errors.home_page = 'URL должен начинаться с http:// або https://'
    valid = false
  }

  if (!form.captcha_answer.trim()) {
    errors.captcha = 'Введите ответ CAPTCHA.'
    valid = false
  }

  if (!form.text.trim()) {
    errors.text = 'Текст является обязательным полем.'
    valid = false
  }

  if (form.attachment && form.attachment.size > 100 * 1024) {
    errors.attachment = 'Файл превышает 100 КБ.'
    valid = false
  }

  return valid
}

// --- Відправка ---
async function submitForm() {
  if (!validate()) return

  submitting.value = true

  const data = new FormData()
  data.append('user_name',     form.user_name)
  data.append('email',         form.email)
  data.append('captcha_answer', form.captcha_answer)
  data.append('text',          form.text)
  if (form.home_page)   data.append('home_page',   form.home_page)
  if (props.parentId)   data.append('parent',       props.parentId)
  if (form.image)       data.append('image',        form.image)
  if (form.attachment)  data.append('attachment',   form.attachment)

  try {
    await api.createComment(data)
    emit('submitted')
  } catch (err) {
    if (err.response?.data) {
      // Переносимо серверні помилки у fields
      const data = err.response.data
      if (data.captcha)    errors.captcha    = data.captcha
      if (data.user_name)  errors.user_name  = data.user_name[0] || data.user_name
      if (data.email)      errors.email      = data.email[0] || data.email
      if (data.text)       errors.text       = data.text[0] || data.text
      if (data.image)      errors.image      = data.image[0] || data.image
      if (data.attachment) errors.attachment = data.attachment[0] || data.attachment
      if (data.non_field_errors) errors.general = data.non_field_errors[0]
      // Після невдачі оновлюємо CAPTCHA
      await loadCaptcha()
    } else {
      errors.general = 'Ошибка сервера. Попробуйте позже.'
    }
  } finally {
    submitting.value = false
  }
}

// --- Ініціалізація ---
onMounted(() => {
  loadCaptcha()
})
</script>

<style scoped>
.comment-form { padding: 20px 24px 24px; }

/* Вкладки */
.form-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 2px solid #e8eaf0;
  padding-bottom: 8px;
}
.tab-btn {
  padding: 6px 18px;
  border: none;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  color: #888;
  background: #f0f0f0;
  transition: background 0.15s;
}
.tab-btn.active { background: #4f8ef7; color: #fff; }

/* Прев'ю */
.preview-pane { padding: 8px 0; }
.preview-bubble {
  background: #f8f9ff;
  border-left: 3px solid #4f8ef7;
  border-radius: 8px;
  padding: 16px;
}
.preview-meta { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px; }
.preview-meta strong { color: #2d3436; }
.preview-email { color: #4f8ef7; }
.preview-text { font-size: 0.95rem; line-height: 1.6; }
.preview-text :deep(code)   { background: #eee; padding: 1px 5px; border-radius: 4px; }
.preview-text :deep(strong) { font-weight: 700; }
.preview-text :deep(i)      { font-style: italic; }
.preview-text :deep(a)      { color: #4f8ef7; }

/* Форма */
.form-body { display: flex; flex-direction: column; gap: 0; }
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
@media (max-width: 560px) { .form-row { grid-template-columns: 1fr; } }

.req { color: #e74c3c; }

/* CAPTCHA */
.captcha-group {}
.captcha-row { display: flex; align-items: center; gap: 10px; margin-top: 4px; }
.captcha-img {
  border: 2px solid #dde3f5;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
  height: 60px;
}
.captcha-img:hover { border-color: #4f8ef7; }
.captcha-placeholder {
  padding: 12px 20px;
  border: 2px dashed #ccc;
  border-radius: 8px;
  cursor: pointer;
  color: #888;
  font-size: 0.85rem;
}
.captcha-placeholder:hover { border-color: #4f8ef7; color: #4f8ef7; }
.captcha-refresh { font-size: 1.1rem; padding: 6px 10px; }

/* Підказка */
.text-hint { font-size: 0.76rem; color: #aaa; margin-top: 4px; }

/* Прев'ю зображення */
.img-preview { margin-top: 8px; }
.img-preview img { max-width: 160px; border-radius: 8px; border: 2px solid #e0e7ff; }

/* Файл вибраний */
.file-selected {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #555;
  padding: 4px 8px;
  border: 1.5px dashed #b0c4ff;
  border-radius: 6px;
  display: inline-block;
}

.general-error { margin-bottom: 8px; }

/* Футер */
.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
  border-top: 1px solid #f0f0f0;
  padding-top: 14px;
}
</style>

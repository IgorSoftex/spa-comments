# SPA Комментарии

SPA-приложение для оставления комментариев с каскадными ответами, реализованное на Django + Vue 3.

---

## Технологии

**Backend:**
- Python 3.11
- Django 4.2 + Django REST Framework 3.14
- Django Channels 4.0 + Daphne 4.0 (WebSocket / ASGI)
- SQLite (база данных)
- Pillow 10.1 (обработка и уменьшение изображений)
- bleach 6.1 (очистка HTML, защита от XSS)
- WhiteNoise 6.6 (раздача статических файлов)
- django-cors-headers 4.3

**Frontend:**
- Vue 3 (Composition API, `<script setup>`)
- Vite 5
- Axios

**Инфраструктура:**
- Docker + Docker Compose
- nginx (обратный прокси, раздача статики фронтенда)

---

## Функциональность

- Добавление комментариев с полями: User Name, E-mail, Home page, CAPTCHA, Text
- Каскадные ответы любой глубины вложенности
- Таблица корневых комментариев с сортировкой по полям: User Name, E-mail, дата (по возрастанию и убыванию)
- Пагинация — 25 комментариев на страницу
- Сортировка по умолчанию — LIFO (новые первыми)
- Прикрепление изображений (JPG, GIF, PNG) с автоматическим пропорциональным уменьшением до 320×240 пикселей
- Прикрепление текстовых файлов (TXT, макс. 100 КБ)
- Lightbox для просмотра прикреплённых файлов (изображений и текста)
- Предпросмотр сообщения перед отправкой (без перезагрузки страницы)
- Панель HTML-тегов: `[i]`, `[strong]`, `[code]`, `[a]`
- Защита от XSS-атак (bleach на сервере)
- Защита от SQL-инъекций (Django ORM)
- Серверная CAPTCHA (генерация через Pillow, хранение в сессии Django)
- Валидация данных на стороне клиента и сервера
- WebSocket — живое обновление списка при добавлении нового комментария

---

## Запуск через Docker

### Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) установлен и запущен
- Git

### Шаги

# 1. Клонировать репозиторий
git clone <URL репозитория>
cd spa-comments

# 2. Собрать и запустить контейнеры
docker-compose up --build

# 3. Открыть сайт
#    http://localhost:8888/

# 4. Django-админка
#    http://localhost:8888/admin/

При первом запуске создайте суперпользователя (пока контейнеры запущены, в отдельном терминале):

docker-compose exec backend python manage.py createsuperuser

---

## Локальный запуск (для разработки)

### Backend

cd backend

# Создать и активировать виртуальное окружение
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# Установить зависимости
pip install -r requirements.txt

# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Запустить через Daphne (поддерживает WebSocket)
daphne -p 8000 config.asgi:application

### Frontend

cd frontend

npm install
npm run dev
# Открыть http://localhost:5173/

> При локальном запуске фронтенд проксирует запросы `/api/` и `/ws/` на `http://localhost:8000`
> через настройки Vite в `vite.config.js`.

---

## Структура проекта

spa-comments/
├── backend/
│   ├── apps/
│   │   └── comments/
│   │       ├── models.py        # Модель Comment, авторесайз изображений
│   │       ├── serializers.py   # Валидация данных, сериализация
│   │       ├── views.py         # API-обработчики, генерация CAPTCHA
│   │       ├── consumers.py     # WebSocket consumer (Django Channels)
│   │       ├── routing.py       # WebSocket URL-маршруты
│   │       └── urls.py          # HTTP URL-маршруты
│   ├── config/
│   │   ├── settings.py          # Настройки Django
│   │   ├── urls.py              # Корневые URL
│   │   ├── asgi.py              # ASGI-конфигурация (HTTP + WebSocket)
│   │   └── wsgi.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.vue              # Корневой компонент, WebSocket, модальное окно
│   │   ├── main.js
│   │   ├── api/
│   │   │   └── comments.js      # Axios: все HTTP-запросы к API
│   │   └── components/
│   │       ├── CommentList.vue  # Таблица комментариев с сортировкой
│   │       ├── CommentItem.vue  # Рекурсивный компонент ответов
│   │       ├── CommentForm.vue  # Форма: поля, CAPTCHA, файлы, превью
│   │       ├── Pagination.vue   # Пагинация
│   │       └── TagToolbar.vue   # Панель HTML-тегов
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── nginx.conf               # Конфигурация nginx для Docker
│   └── Dockerfile
└── docker-compose.yml

---

## API Endpoints

| Метод  | URL                              | Описание                                      |
|--------|----------------------------------|-----------------------------------------------|
| GET    | `/api/comments/`                 | Список корневых комментариев (пагинация, сортировка) |
| POST   | `/api/comments/`                 | Создать комментарий                           |
| GET    | `/api/comments/<id>/`            | Один комментарий со всеми вложенными ответами |
| GET    | `/api/comments/<id>/replies/`    | Ответы на комментарий (рекурсивно)            |
| GET    | `/api/captcha/`                  | Получить CAPTCHA (base64 PNG)                 |
| POST   | `/api/captcha/verify/`           | Проверить ответ CAPTCHA                       |
| GET    | `/admin/`                        | Django-админка                                |
| WS     | `/ws/comments/`                  | WebSocket для живых обновлений                |

### Параметры GET `/api/comments/`

| Параметр     | Значения                          | По умолчанию  |
|--------------|-----------------------------------|---------------|
| `page`       | номер страницы                    | `1`           |
| `sort_by`    | `created_at`, `user_name`, `email`| `created_at`  |
| `sort_order` | `asc`, `desc`                     | `desc`        |

---

## Разрешённые HTML-теги в тексте

В тексте комментария разрешены следующие теги:

<a href="" title=""> ... </a>
<code> ... </code>
<i> ... </i>
<strong> ... </strong>

Все остальные теги автоматически удаляются библиотекой **bleach** на сервере.

---

## Продакшн-настройки

Перед развёртыванием на сервере в `backend/config/settings.py` замените:

SECRET_KEY = 'ваш-секретный-ключ-минимум-50-символов'
DEBUG = False
ALLOWED_HOSTS = ['ваш-домен.com']

---

## Самопроверка

Для проверки что всё работает с нуля:

git clone <URL репозитория>
cd spa-comments
docker-compose up --build
# Открыть http://localhost:8888/

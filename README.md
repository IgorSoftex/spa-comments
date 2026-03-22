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

## Запуск через Docker (рекомендуется)

### Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) установлен и запущен
- Git

### Шаги

```bash
# 1. Клонировать репозиторий
git clone https://github.com/IgorSoftex/spa-comments.git
cd spa-comments

# 2. Собрать и запустить контейнеры
docker-compose up --build

# 3. Открыть сайт
#    http://localhost:8888/

# 4. Django-админка
#    http://localhost:8888/admin/
```

При первом запуске создайте суперпользователя (пока контейнеры запущены, в отдельном терминале):

```bash
docker-compose exec backend python manage.py createsuperuser
```

---

## Локальный запуск (для разработки)

### Backend

```bash
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
```

### Frontend

```bash
cd frontend

npm install
npm run dev
# Открыть http://localhost:5173/
```

> При локальном запуске фронтенд проксирует запросы `/api/` и `/ws/` на `http://localhost:8000`
> через настройки Vite в `vite.config.js`.

---

## Структура проекта

```
spa-comments/
├── backend/
│   ├── apps/
│   │   ├── __init__.py
│   │   └── comments/
│   │       ├── admin.py
│   │       ├── apps.py
│   │       ├── consumers.py     # WebSocket consumer (Django Channels)
│   │       ├── models.py        # Модель Comment, авторесайз изображений
│   │       ├── routing.py       # WebSocket URL-маршруты
│   │       ├── serializers.py   # Валидация данных, сериализация
│   │       ├── tests.py
│   │       ├── urls.py          # HTTP URL-маршруты
│   │       ├── views.py         # API-обработчики, генерация CAPTCHA
│   │       └── migrations/
│   │           └── 0001_initial.py
│   ├── config/
│   │   ├── asgi.py              # ASGI-конфигурация (HTTP + WebSocket)
│   │   ├── settings.py          # Настройки Django
│   │   ├── urls.py              # Корневые URL
│   │   └── wsgi.py
│   ├── db.sqlite3               # База данных SQLite
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.vue              # Корневой компонент, WebSocket, модальное окно
│   │   ├── main.js
│   │   ├── api/
│   │   │   └── comments.js      # Axios: все HTTP-запросы к API
│   │   └── components/
│   │       ├── CommentForm.vue  # Форма: поля, CAPTCHA, файлы, превью
│   │       ├── CommentItem.vue  # Рекурсивный компонент ответов
│   │       ├── CommentList.vue  # Таблица комментариев с сортировкой
│   │       ├── Pagination.vue   # Пагинация
│   │       └── TagToolbar.vue   # Панель HTML-тегов
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── nginx.conf               # Конфигурация nginx для Docker
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## API Endpoints

| Метод | URL                           | Описание                                           |
|-------|-------------------------------|----------------------------------------------------|
| GET   | `/api/comments/`              | Список корневых комментариев (пагинация, сортировка) |
| POST  | `/api/comments/`              | Создать комментарий                                |
| GET   | `/api/comments/<id>/`         | Один комментарий со всеми вложенными ответами      |
| GET   | `/api/comments/<id>/replies/` | Ответы на комментарий (рекурсивно)                 |
| GET   | `/api/captcha/`               | Получить CAPTCHA (base64 PNG)                      |
| POST  | `/api/captcha/verify/`        | Проверить ответ CAPTCHA                            |
| GET   | `/admin/`                     | Django-админка                                     |
| WS    | `/ws/comments/`               | WebSocket для живых обновлений                     |

### Параметры GET `/api/comments/`

| Параметр     | Значения                           | По умолчанию |
|--------------|------------------------------------|--------------|
| `page`       | номер страницы                     | `1`          |
| `sort_by`    | `created_at`, `user_name`, `email` | `created_at` |
| `sort_order` | `asc`, `desc`                      | `desc`       |

---

## Разрешённые HTML-теги в тексте

В тексте комментария разрешены следующие теги:

```html
<a href="" title=""> ... </a>
<code> ... </code>
<i> ... </i>
<strong> ... </strong>
```

Все остальные теги автоматически удаляются библиотекой **bleach** на сервере.

---

## Продакшн-настройки

Перед развёртыванием на сервере в `backend/config/settings.py` замените:

```python
SECRET_KEY = 'ваш-секретный-ключ-минимум-50-символов'
DEBUG = False
ALLOWED_HOSTS = ['ваш-домен.com']
```

---

## Самопроверка

Для проверки что всё работает с нуля:

```bash
git clone https://github.com/IgorSoftex/spa-comments.git
cd spa-comments
docker-compose up --build
# Открыть http://localhost:8888/
```

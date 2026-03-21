# Главный конфигурационный файл Django.
# Здесь определяются все настройки проекта:
# подключённые приложения, база данных, middleware, статические файлы и т.д.

import os
from pathlib import Path

# BASE_DIR — корневая папка проекта (папка backend/).
# Path(__file__) — путь к этому файлу (config/settings.py)
# .resolve() — превращает относительный путь в абсолютный
# .parent.parent — поднимаемся на два уровня вверх: config/ → backend/
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ Django — используется для криптографических операций:
# подписи сессий, токенов, CSRF-защиты.
# В продакшене ОБЯЗАТЕЛЬНО менять на длинный случайный ключ
# и хранить в переменной окружения, а не в коде!
SECRET_KEY = 'django-insecure-change-me-in-production'

# Режим отладки — показывает подробные ошибки в браузере.
# В продакшене ОБЯЗАТЕЛЬНО устанавливать False,
# иначе пользователи увидят внутренний код проекта.
DEBUG = True

# Список разрешённых хостов для доступа к сайту.
# '*' — разрешаем все хосты (подходит для разработки).
# В продакшене указывать конкретные домены: ['example.com', 'www.example.com']
ALLOWED_HOSTS = ['*']

# ==================== ПРИЛОЖЕНИЯ ====================
# Список всех подключённых Django-приложений.
# Django загружает их в указанном порядке.
INSTALLED_APPS = [
    'django.contrib.admin',        # административная панель /admin/
    'django.contrib.auth',         # система аутентификации (пользователи, пароли)
    'django.contrib.contenttypes', # фреймворк типов контента
    'django.contrib.sessions',     # хранение сессий (используем для CAPTCHA)
    'django.contrib.messages',     # система сообщений (flash messages)
    'django.contrib.staticfiles',  # управление статическими файлами (CSS, JS)

    # Сторонние библиотеки
    'rest_framework',   # Django REST Framework — инструменты для построения API
    'corsheaders',      # CORS — разрешаем запросы с фронтенда (другой порт/домен)
    'channels',         # Django Channels — поддержка WebSocket

    # Наши приложения
    'apps.comments',    # приложение комментариев
]

# ==================== MIDDLEWARE ====================
# Middleware — это цепочка обработчиков, через которые проходит
# каждый HTTP-запрос (до view) и каждый ответ (после view).
# Порядок важен — обрабатываются сверху вниз при запросе
# и снизу вверх при ответе.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise — раздача статических файлов напрямую через Django/Daphne
    # без отдельного nginx. ДОЛЖЕН стоять сразу после SecurityMiddleware.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # CORS — должен стоять перед CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Главный файл маршрутизации URL проекта
ROOT_URLCONF = 'config.urls'

# ==================== ШАБЛОНЫ ====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Папки где Django ищет HTML-шаблоны
        'DIRS': [],
        # APP_DIRS: True — Django также ищет шаблоны в папке templates/
        # внутри каждого приложения
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI — интерфейс для синхронных серверов (gunicorn, uwsgi).
# В нашем проекте используется ASGI (Daphne), но это поле обязательно.
WSGI_APPLICATION = 'config.wsgi.application'

# ASGI — интерфейс для асинхронных серверов (Daphne).
# Используется для поддержки WebSocket через Django Channels.
ASGI_APPLICATION = 'config.asgi.application'

# ==================== БАЗА ДАННЫХ ====================
# SQLite — файловая база данных, идеальна для разработки.
# Вся база хранится в одном файле db.sqlite3 в папке backend/.
# В продакшене обычно используют PostgreSQL или MySQL.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==================== DJANGO CHANNELS ====================
# Channel Layer — шина сообщений между consumers (WebSocket-обработчиками).
# InMemoryChannelLayer хранит сообщения в оперативной памяти.
# Подходит для разработки и небольших проектов.
# В продакшене с несколькими серверами используют RedisChannelLayer.
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ==================== CORS ====================
# CORS (Cross-Origin Resource Sharing) — механизм безопасности браузера.
# Браузер блокирует запросы с одного домена/порта к другому.
# Наш фронтенд (Vue на порту 5173) делает запросы к бекенду (Django на порту 8000).
# Это разные порты — браузер считает их разными "источниками" и блокирует.
# CORS_ALLOW_ALL_ORIGINS = True — разрешаем запросы с любого источника.
# В продакшене лучше указать конкретные домены через CORS_ALLOWED_ORIGINS.
CORS_ALLOW_ALL_ORIGINS = True

# Разрешаем передачу cookies (нужно для сессий — капча хранится в сессии)
CORS_ALLOW_CREDENTIALS = True

# ==================== СТАТИЧЕСКИЕ ФАЙЛЫ ====================
# Статические файлы — CSS, JavaScript, картинки для интерфейса.

# URL по которому браузер запрашивает статику: /static/style.css
STATIC_URL = '/static/'

# Папка куда Django собирает все статические файлы командой collectstatic.
# WhiteNoise раздаёт файлы именно из этой папки.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ==================== МЕДИАФАЙЛЫ ====================
# Медиафайлы — файлы загруженные пользователями (изображения, документы).

# URL по которому браузер запрашивает медиафайлы: /media/images/photo.jpg
MEDIA_URL = '/media/'

# Папка где хранятся загруженные файлы (backend/media/)
MEDIA_ROOT = BASE_DIR / 'media'

# ==================== СЕССИИ ====================
# Используем сессии на основе базы данных.
# Сессии нужны для хранения текста CAPTCHA между запросами:
# GET /api/captcha/ — сохраняем текст в сессии
# POST /api/captcha/verify/ — проверяем текст из сессии
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ==================== ЛОКАЛИЗАЦИЯ ====================
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True   # интернационализация (переводы)
USE_TZ = True     # использовать временные зоны

# Тип поля первичного ключа по умолчанию для моделей.
# BigAutoField — 64-битное целое число (до 9 квинтиллионов записей).
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== DRF НАСТРОЙКИ ====================
REST_FRAMEWORK = {
    # Отключаем стандартные классы аутентификации (BasicAuthentication + SessionAuthentication).
    # SessionAuthentication принудительно требует CSRF-токен для всех POST-запросов.
    # Так как наш API публичный (без логина пользователей), аутентификация не нужна.
    # Сессии Django при этом продолжают работать — капча хранится в сессии независимо.
    'DEFAULT_AUTHENTICATION_CLASSES': [],

    # Убираем ограничения доступа — API открытый.
    'DEFAULT_PERMISSION_CLASSES': [],

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
}

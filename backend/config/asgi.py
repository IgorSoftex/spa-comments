# ASGI (Asynchronous Server Gateway Interface) — асинхронный интерфейс
# между веб-сервером и Django-приложением.
#
# Это точка входа для сервера Daphne. При запуске Daphne читает этот файл
# и узнаёт как обрабатывать входящие соединения.
#
# ASGI умеет работать с двумя протоколами одновременно:
#   - HTTP  — обычные запросы браузера (GET, POST...)
#   - WebSocket — постоянные двусторонние соединения
#
# Старый интерфейс WSGI (gunicorn, uwsgi) поддерживает только HTTP.
# ASGI (Daphne) поддерживает и HTTP, и WebSocket — поэтому мы его используем.

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Указываем Django где найти файл настроек.
# Это нужно сделать ДО импорта чего-либо из Django,
# иначе Django не будет знать какие настройки использовать.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Импортируем WebSocket-маршруты из нашего приложения.
# Делаем это ПОСЛЕ установки DJANGO_SETTINGS_MODULE,
# чтобы Django уже знал свои настройки при загрузке модулей.
from apps.comments.routing import websocket_urlpatterns

# application — главный объект ASGI-приложения.
# Daphne вызывает именно его для каждого входящего соединения.
#
# ProtocolTypeRouter — маршрутизатор по типу протокола.
# Смотрит на тип входящего соединения и направляет его
# в нужный обработчик.
application = ProtocolTypeRouter({

    # HTTP-запросы обрабатывает стандартное Django-приложение.
    # get_asgi_application() возвращает обычный Django ASGI-обработчик,
    # который знает про urls.py, views.py, middleware и т.д.
    'http': get_asgi_application(),

    # WebSocket-соединения обрабатывает Django Channels.
    # AuthMiddlewareStack — промежуточный слой, который добавляет
    # информацию об аутентифицированном пользователе в scope
    # (контекст WebSocket-соединения), аналогично request.user в HTTP.
    # URLRouter — маршрутизатор по URL, аналог urls.py для WebSocket.
    # Смотрит на URL соединения и находит нужный consumer в websocket_urlpatterns.
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # из apps/comments/routing.py
        )
    ),
})

"""
Как Daphne использует этот файл
Daphne запускается и читает config/asgi.py
        ↓
Приходит соединение от браузера
        ↓
ProtocolTypeRouter смотрит на тип:

  HTTP запрос (GET /api/comments/)
        ↓
  get_asgi_application() → urls.py → views.py → JSON

  WebSocket (ws://localhost/ws/comments/)
        ↓
  AuthMiddlewareStack → URLRouter → routing.py → CommentConsumer
"""

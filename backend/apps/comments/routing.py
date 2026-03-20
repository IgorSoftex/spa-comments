# Маршрутизация WebSocket-соединений — аналог urls.py, но для WebSocket.
# Обычный urls.py обрабатывает HTTP-запросы (GET, POST...),
# а routing.py обрабатывает WebSocket-соединения (ws://, wss://).
from django.urls import re_path

# Импортируем наш WebSocket-обработчик
from . import consumers

# Список WebSocket-маршрутов.
# Браузер подключается по адресу ws://localhost/ws/comments/
# Django Channels ищет совпадение в этом списке и передаёт
# соединение соответствующему consumer-классу.
websocket_urlpatterns = [

    # re_path использует регулярное выражение для совпадения URL.
    # r'ws/comments/$' означает:
    #   ws/comments/ — буквальный путь
    #   $ — конец строки (URL должен заканчиваться именно здесь)
    # CommentConsumer.as_asgi() — преобразует класс в ASGI-приложение,
    # аналогично тому как .as_view() работает для обычных Django views
    re_path(r'ws/comments/$', consumers.CommentConsumer.as_asgi()),
]

"""
Разница между urls.py и routing.py
HTTP-запрос от браузера:
GET http://localhost/api/comments/
        ↓
config/urls.py → apps/comments/urls.py → CommentListCreateView

WebSocket-соединение от браузера:
ws://localhost/ws/comments/
        ↓
config/asgi.py → apps/comments/routing.py → CommentConsumer
"""
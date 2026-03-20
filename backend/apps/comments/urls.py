# Модуль для определения URL-маршрутов (роутинг запросов)
from django.urls import path

# Импортируем наши view-классы, которые обрабатывают HTTP-запросы
from .views import (
    CommentListCreateView,  # GET /api/comments/ и POST /api/comments/
    CommentDetailView,      # GET /api/comments/<id>/
    CaptchaView,            # GET /api/captcha/ — генерация картинки с капчей
    CaptchaVerifyView,      # POST /api/captcha/verify/ — проверка текста капчи
)

# Список URL-маршрутов этого приложения.
# Django просматривает этот список сверху вниз и останавливается
# на первом совпадении с URL из запроса браузера.
urlpatterns = [

    # GET  /api/comments/  — вернуть список корневых комментариев (без родителя)
    # POST /api/comments/  — создать новый комментарий
    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),

    # GET /api/comments/<id>/  — вернуть один комментарий со всеми вложенными
    # ответами (replies). <int:pk> — это целочисленный параметр, Django автоматически
    # передаёт его в view как переменную pk (primary key — первичный ключ в БД)
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),

    # GET /api/captcha/  — сгенерировать новую картинку капчи.
    # Pillow рисует изображение с случайным текстом, текст сохраняется в сессии,
    # а браузеру возвращается PNG-картинка
    path('captcha/', CaptchaView.as_view(), name='captcha'),

    # POST /api/captcha/verify/  — проверить текст, который пользователь
    # ввёл с картинки капчи. Сравниваем с текстом из сессии.
    # Возвращает {'valid': true} или {'valid': false, 'error': '...'}
    path('captcha/verify/', CaptchaVerifyView.as_view(), name='captcha-verify'),
]

"""
Как это работает вместе
Браузер отправляет:            Django ищет совпадение:
GET /api/comments/         →   comments/          → CommentListCreateView
POST /api/comments/        →   comments/          → CommentListCreateView
GET /api/comments/5/       →   comments/<int:pk>/ → CommentDetailView (pk=5)
GET /api/captcha/          →   captcha/           → CaptchaView
POST /api/captcha/verify/  →   captcha/verify/    → CaptchaVerifyView
"""
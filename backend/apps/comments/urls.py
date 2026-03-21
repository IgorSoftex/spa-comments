from django.urls import path
from .views import (
    CommentListCreateView,
    CommentDetailView,
    CommentRepliesView,
    CaptchaView,
    CaptchaVerifyView,
)

urlpatterns = [
    # GET /api/comments/        — список коментарів з пагінацією
    # POST /api/comments/       — створити новий коментар
    path('comments/', CommentListCreateView.as_view(), name='comment-list-create'),

    # GET /api/comments/<id>/   — один коментар з вкладеними replies
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),

    # GET /api/comments/<id>/replies/ — коментар з усіма відповідями
    # Використовується при натисканні кнопки "Відповіді" в таблиці
    path('comments/<int:pk>/replies/', CommentRepliesView.as_view(), name='comment-replies'),

    # GET  /api/captcha/         — отримати base64-зображення капчі
    path('captcha/', CaptchaView.as_view(), name='captcha'),

    # POST /api/captcha/verify/  — перевірити текст капчі
    path('captcha/verify/', CaptchaVerifyView.as_view(), name='captcha-verify'),
]
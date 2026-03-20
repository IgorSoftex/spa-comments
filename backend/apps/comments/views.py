"""
View – это обработчик HTTP-запросов.
Браузер посылает запрос → view получает его,
обращается в базу данных через модель,
сериализирует данные → возвращает JSON
"""
import io
import random
import string

# Python Imaging Library
from PIL import Image, ImageDraw, ImageFont
from django.http import HttpResponse
# DRF (Django REST Framework) содержит набор готовых классов,
# уже умеющих обрабатывать стандартные запросы
# DRF – это набор инструментов для построения API
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment
from .serializers import CommentSerializer, CommentDetailSerializer


class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/comments/        — список корневых комментариев
    POST /api/comments/        — создать новый комментарий
    """
    serializer_class = CommentSerializer

    def get_queryset(self):
        # Возвращаем только корневые комментарии (без родителя)
        queryset = Comment.objects.filter(parent=None)

        # Сортировка: ?ordering=created_at (старые) или -created_at (новые)
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = ['created_at', '-created_at', 'user_name', '-user_name', 'email', '-email']
        if ordering in allowed:
            queryset = queryset.order_by(ordering)

        return queryset


class CommentDetailView(generics.RetrieveAPIView):
    """
    GET /api/comments/<id>/    — один комментарий со всеми вложенными replies
    """
    queryset = Comment.objects.all()
    serializer_class = CommentDetailSerializer


class CaptchaView(APIView):
    """
    GET /api/captcha/          — генерирует картинку CAPTCHA и сохраняет текст в сессии
    """

    def get(self, request):
        # Генерируем случайный текст из 5 символов
        characters = string.ascii_uppercase + string.digits
        captcha_text = ''.join(random.choices(characters, k=5))

        # Сохраняем текст в сессии для проверки позже
        request.session['captcha'] = captcha_text

        # Создаём картинку через Pillow
        width, height = 120, 40
        image = Image.new('RGB', (width, height), color=(240, 240, 240))
        draw = ImageDraw.Draw(image)

        # Рисуем шум (случайные точки)
        for _ in range(500):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill=(random.randint(100, 200),) * 3)

        # Рисуем текст
        draw.text((10, 8), captcha_text, fill=(30, 30, 30))

        # Конвертируем в байты и отправляем как PNG
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)

        return HttpResponse(buffer, content_type='image/png')


class CaptchaVerifyView(APIView):
    """
    POST /api/captcha/verify/  — проверяет введённый пользователем текст CAPTCHA
    """

    def post(self, request):
        user_input = request.data.get('captcha', '').strip().upper()
        correct = request.session.get('captcha', '')

        if user_input == correct:
            # Удаляем капчу из сессии после успешной проверки
            del request.session['captcha']
            return Response({'valid': True})

        return Response(
            {'valid': False, 'error': 'Неверный текст CAPTCHA.'},
            status=status.HTTP_400_BAD_REQUEST
        )

"""
View – это обработчик HTTP-запросов.
Браузер посылает запрос → view получает его,
обращается в базу данных через модель,
сериализирует данные → возвращает JSON
"""
import io
import base64
import random
import string

from PIL import Image, ImageDraw
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment
from .serializers import CommentSerializer, CommentDetailSerializer


class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/comments/   — список корневых комментариев с пагинацией
    POST /api/comments/   — создать новый комментарий
    """
    serializer_class = CommentSerializer

    def get_queryset(self):
        # Возвращаем только корневые комментарии (без родителя)
        queryset = Comment.objects.filter(parent=None)

        # Сортировка через параметры sort_by и sort_order.
        # sort_by    — поле: created_at, user_name, email
        # sort_order — направление: asc (возрастание) или desc (убывание)
        sort_by = self.request.query_params.get('sort_by', 'created_at')
        sort_order = self.request.query_params.get('sort_order', 'desc')

        allowed_fields = ['created_at', 'user_name', 'email']
        if sort_by in allowed_fields:
            # Минус перед полем означает обратный порядок (DESC)
            prefix = '-' if sort_order == 'desc' else ''
            queryset = queryset.order_by(f'{prefix}{sort_by}')

        return queryset


class CommentDetailView(generics.RetrieveAPIView):
    """
    GET /api/comments/<id>/   — один комментарий со всеми вложенными replies
    """
    queryset = Comment.objects.all()
    serializer_class = CommentDetailSerializer


class CommentRepliesView(generics.RetrieveAPIView):
    """
    GET /api/comments/<id>/replies/   — возвращает комментарий
    вместе со всеми вложенными ответами (рекурсивно).
    Используется когда пользователь нажимает "Відповіді" в таблице.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentDetailSerializer


class CaptchaView(APIView):
    """
    GET /api/captcha/   — генерирует CAPTCHA и возвращает base64-изображение.
    Возвращает JSON: { "image": "data:image/png;base64,..." }
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

        # Рисуем текст капчи
        draw.text((10, 8), captcha_text, fill=(30, 30, 30))

        # Конвертируем изображение в base64-строку.
        # Браузер может отображать base64 напрямую через src="data:image/png;base64,..."
        # Это удобнее чем отдельный URL — не нужен дополнительный HTTP-запрос.
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        return Response({
            'image': f'data:image/png;base64,{img_base64}'
        })


class CaptchaVerifyView(APIView):
    """
    POST /api/captcha/verify/   — проверяет текст введённый пользователем.
    Принимает: { "captcha": "ABC12" }
    Возвращает: { "valid": true } или { "valid": false, "error": "..." }
    """

    def post(self, request):
        user_input = request.data.get('captcha', '').strip().upper()
        correct = request.session.get('captcha', '')

        if user_input == correct:
            del request.session['captcha']
            return Response({'valid': True})

        return Response(
            {'valid': False, 'error': 'Невірний текст CAPTCHA.'},
            status=status.HTTP_400_BAD_REQUEST
        )

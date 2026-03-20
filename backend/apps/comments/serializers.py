# регулярные выражения
import re
# Библиотека bleach для очистки HTML от опасного кода (XSS атак (Cross-Site Scripting)...)
# В нашем проекте разрешено только четыре тега
import bleach
from rest_framework import serializers # импорт модуля сериализаторов из DRF
from .models import Comment, ALLOWED_TAGS, ALLOWED_ATTRIBUTES

""" Сериализатор – это "переводчик" между Python-объектами и JSON.
	Python-объект Comment  →  сериализатор  →  JSON для браузера
	JSON от браузера       →  сериализатор  →  Python-объект для сохранения
"""
class CommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка комментариев (без вложенных replies).
    """
    replies_count = serializers.SerializerMethodField()

    class Meta:
        """
        Meta – встроенный класс-настройки.
        Django REST Framework ищет класс с таким названием
        внутри сериализатора, чтобы узнать, как он настроен
        """
        model = Comment
        fields = [
            'id', 'user_name', 'email', 'home_page', 'text',
            'parent', 'created_at', 'image', 'attachment', 'replies_count'
        ]
        read_only_fields = ['created_at', 'replies_count']

    def get_replies_count(self, obj):
        """Количество прямых ответов на этот комментарий."""
        return obj.replies.count()

    def validate_user_name(self, value):
        """Только латиница, цифры и дефис."""
        if not re.match(r'^[a-zA-Z0-9\-]+$', value):
            raise serializers.ValidationError(
                'Имя может содержать только латинские буквы, цифры и дефисы.'
            )
        return value

    def validate_text(self, value):
        """Очищаем HTML – оставляем только разрешенные теги."""
        cleaned = bleach.clean(
            value,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True,
            strip_comments=True
        )
        if not cleaned.strip():
            raise serializers.ValidationError('Текст комментария не может быть пустым.')
        return cleaned

    def validate_image(self, value):
        """Изображение: только JPEG/PNG, максимум 1 МБ."""
        if value:
            allowed_types = ['image/jpeg', 'image/png']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError('Разрешено только JPEG или PNG.')
            if value.size > 1 * 1024 * 1024:
                raise serializers.ValidationError('Размер изображения не более 1 МБ.')
        return value

    def validate_attachment(self, value):
        """Файл: только TXT или XML, максимум 100 КБ."""
        if value:
            allowed_types = ['text/plain', 'text/xml', 'application/xml']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError('Разрешено только TXT или XML файлы.')
            if value.size > 100 * 1024:
                raise serializers.ValidationError('Размер файла не более 100 КБ.')
        return value


class CommentDetailSerializer(CommentSerializer):
    """Сериализатор для одного комментария с вложенными replies."""
    replies = serializers.SerializerMethodField()

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['replies']

    def get_replies(self, obj):
        """Рекурсивно возвращает все ответы на комментарий."""
        children = obj.replies.all().order_by('-created_at')
        return CommentDetailSerializer(children, many=True, context=self.context).data

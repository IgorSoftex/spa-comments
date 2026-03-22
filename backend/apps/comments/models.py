from django.db import models
import bleach
# Добавляем Pillow для изменения размера изображений
from PIL import Image


ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}


def sanitize_html(text: str) -> str:
    """Очищает HTML: оставляет только разрешенные теги. Защита от XSS."""
    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
        strip_comments=True,
    )


class Comment(models.Model):
    """Основная модель для хранения комментариев."""

    user_name  = models.CharField(max_length=255)
    email      = models.EmailField()
    home_page  = models.URLField(blank=True, null=True)
    text       = models.TextField()

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )

    image = models.ImageField(
        upload_to='images/',
        blank=True,
        null=True,
    )

    attachment = models.FileField(
        upload_to='files/',
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # LIFO по умолчанию

    def __str__(self):
        return f'{self.user_name} ({self.email})'

    def save(self, *args, **kwargs):
        """
        Перед сохранением — очищает HTML.
        После сохранения — уменьшает изображение до 320×240 если нужно.
        """
        self.text = sanitize_html(self.text)
        super().save(*args, **kwargs)

        # Resize после super().save() — файл уже записан на диск,
        # можно открыть через self.image.path
        if self.image:
            self._resize_image_if_needed()

    def _resize_image_if_needed(self):
        """
        Пропорционально уменьшает изображение до 320×240 пикселей.
        Поддерживает JPEG, PNG, GIF согласно требованиям ТЗ.

        Image.thumbnail() — встроенный метод Pillow для пропорционального
        уменьшения. Никогда не увеличивает изображение, только уменьшает.
        Если изображение уже меньше 320×240 — ничего не происходит.
        """
        try:
            img = Image.open(self.image.path)
            max_w, max_h = 320, 240

            # Если изображение уже вписывается в лимит — выходим
            if img.width <= max_w and img.height <= max_h:
                return

            # Запоминаем формат ДО конвертации режима
            # img.format может быть 'JPEG', 'PNG', 'GIF'
            fmt = img.format or 'JPEG'

            # GIF использует режим палитры 'P' (256 цветов).
            # Фильтр LANCZOS не работает с палитрой напрямую —
            # конвертируем в RGBA чтобы получить качественный resize.
            if img.mode == 'P':
                img = img.convert('RGBA')

            # CMYK используется в профессиональных JPEG (типографских).
            # Браузеры не поддерживают CMYK — конвертируем в RGB.
            if img.mode == 'CMYK':
                img = img.convert('RGB')

            # thumbnail() — пропорциональное уменьшение с фильтром LANCZOS.
            # LANCZOS (ранее ANTIALIAS) — лучший фильтр для уменьшения,
            # сохраняет чёткость краёв.
            img.thumbnail((max_w, max_h), Image.LANCZOS)

            # Сохраняем в оригинальном формате
            if fmt == 'GIF':
                # Конвертируем обратно в палитру для сохранения как GIF.
                # ADAPTIVE — Pillow автоматически выбирает 256 лучших цветов.
                img = img.convert('P', palette=Image.ADAPTIVE)
                img.save(self.image.path, format='GIF')

            elif fmt == 'JPEG':
                # JPEG не поддерживает альфа-канал — убираем если есть
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                img.save(self.image.path, format='JPEG', quality=85, optimize=True)

            else:
                # PNG и другие форматы — сохраняем как есть
                img.save(self.image.path)

        except Exception:
            # Если resize по какой-то причине не удался —
            # молча оставляем оригинал, чтобы не сломать сохранение комментария
            pass

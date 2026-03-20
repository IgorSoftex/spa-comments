from django.db import models
# Библиотека bleach для очистки HTML от опасного кода (XSS атак (Cross-Site Scripting)...)
# В нашем проекте разрешено только четыре тега
import bleach


# Разрешены HTML-теги в тексте сообщения
ALLOWED_TAGS = ['a', 'code', 'i', 'strong']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}


def sanitize_html(text: str) -> str:
    """
    Очищает HTML: оставляет только разрешенные теги, остальные удаляет.
    Защита от XSS (Cross-Site Scripting).
    """
    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
        strip_comments=True,
    )


class Comment(models.Model):
    """
    основная модель для хранения комментариев
    """

    # Данные пользователя
    user_name = models.CharField(max_length=255)
    email = models.EmailField()
    home_page = models.URLField(blank=True, null=True)

    # Текст сообщения
    text = models.TextField()

    # Каскадные ответы (ссылка на самого себя)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE, # если удалить комментарий, все его ответы удаляются автоматически
        null=True,
        blank=True,
        related_name='replies',
    )

    # Вложенные файлы
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

    # Дата создания. Устанавливается автоматически при создании записи
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        внутренний класс внутри модели, содержащий настройки для всей модели, а не для отдельного поля
        """
        ordering = ['-created_at']  # LIFO по умолчанию

    def __str__(self):
        """
        специальный метод, определяющий как объект отображается как строка
        """
        return f'{self.user_name} ({self.email})'

    def save(self, *args, **kwargs):
        """
        переопределенный метод, который перед сохранением очищает HTML через bleach
        """
        # Автоматическая очистка HTML перед сохранением
        self.text = sanitize_html(self.text)
        super().save(*args, **kwargs)

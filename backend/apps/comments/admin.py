from django.contrib import admin
from .models import Comment # импортируем нашу модель

# декоратор, который регистрирует модель Comment в админке
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'email', 'parent', 'created_at')
    list_filter = ('created_at',) # фильтр справа в админке, позволяет фильтровать по дате
    search_fields = ('user_name', 'email', 'text') # поле поиска вверху, ищет по user_name, email и text
    ordering = ('-created_at',) # сортировка в админке от более новых до старых

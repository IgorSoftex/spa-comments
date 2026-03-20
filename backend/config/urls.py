# Главный файл маршрутизации URL всего проекта.
# Это "диспетчер" — получает URL от браузера и решает
# куда его направить: в админку, к API, или к медиафайлам.
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # Административная панель Django.
    # /admin/ — стандартный URL для входа в админку.
    # admin.site.urls содержит все маршруты административного раздела.
    path('admin/', admin.site.urls),

    # Подключаем маршруты приложения comments с префиксом /api/.
    # include() загружает все urlpatterns из apps/comments/urls.py
    # и добавляет к ним префикс 'api/'.
    # Итоговые URL будут:
    #   /api/comments/          → CommentListCreateView
    #   /api/comments/<id>/     → CommentDetailView
    #   /api/captcha/           → CaptchaView
    #   /api/captcha/verify/    → CaptchaVerifyView
    path('api/', include('apps.comments.urls')),

]

# Раздача медиафайлов в режиме разработки (DEBUG=True).
# В продакшене медиафайлы раздаёт nginx, а не Django.
# static() добавляет маршрут: /media/<путь> → файл из MEDIA_ROOT
# Например: /media/images/photo.jpg → backend/media/images/photo.jpg
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""
Как собираются все маршруты проекта
config/urls.py  (главный диспетчер)
│
├── /admin/          → Django admin (встроенный)
│
├── /api/            → include('apps.comments.urls')
│     │
│     ├── comments/          → CommentListCreateView
│     ├── comments/<id>/     → CommentDetailView
│     ├── captcha/           → CaptchaView
│     └── captcha/verify/    → CaptchaVerifyView
│
└── /media/<file>    → файл из папки backend/media/ (тольки при DEBUG=True)
"""

"""Главный URL-роутер проекта DiaMed."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('about/', include('apps.about.urls')),
    path('services/', include('apps.services.urls')),
    path('contacts/', include('apps.contacts.urls')),
    path('users/', include('apps.users.urls')),
]

# Подключение медиа-файлов в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

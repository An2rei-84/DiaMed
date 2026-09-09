"""Конфигурация Celery для проекта DiaMed."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diamed.settings")

app = Celery("diamed")

# Читаем настройки с префиксом CELERY_ из settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Задачи ищем в tasks.py каждого приложения
app.autodiscover_tasks()

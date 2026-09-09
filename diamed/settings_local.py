"""Локальные настройки для разработки с SQLite."""

from .settings import *

# Используем SQLite для локальной разработки
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# В разработке и тестах задачи выполняются синхронно, без брокера
CELERY_TASK_ALWAYS_EAGER = True

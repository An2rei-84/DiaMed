"""Конфигурация core приложения."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Конфигурация главного приложения."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Главная страница'

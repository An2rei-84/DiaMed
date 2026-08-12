"""Конфигурация about приложения."""

from django.apps import AppConfig


class AboutConfig(AppConfig):
    """Конфигурация приложения 'О компании'."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.about'
    verbose_name = 'О компании'

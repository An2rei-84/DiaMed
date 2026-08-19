"""Конфигурация services приложения."""

from django.apps import AppConfig


class ServicesConfig(AppConfig):
    """Конфигурация приложения услуг."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.services"
    verbose_name = "Услуги"

"""Конфигурация contacts приложения."""

from django.apps import AppConfig


class ContactsConfig(AppConfig):
    """Конфигурация приложения контактов."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.contacts'
    verbose_name = 'Контакты'

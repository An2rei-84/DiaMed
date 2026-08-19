"""Админка contacts приложения."""

from django.contrib import admin

from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Админка для контактов."""

    list_display = ["address", "phone", "email"]
    fieldsets = [
        ["Основная информация", {"fields": ["address", "phone", "email", "working_hours"]}],
        ["Карта", {"fields": ["map_url", "map_embed"]}],
    ]

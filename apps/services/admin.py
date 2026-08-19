"""Админка services приложения."""

from django.contrib import admin

from .models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """Админка для категорий услуг."""

    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Админка для услуг."""

    list_display = ["name", "category", "price", "duration", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = []

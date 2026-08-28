"""Админка core приложения."""

from django.contrib import admin

from .models import ContactForm


@admin.register(ContactForm)
class ContactFormAdmin(admin.ModelAdmin):
    """Админка для заявок."""

    list_display = ["name", "email", "created_at", "is_processed"]
    list_filter = ["is_processed", "created_at"]
    search_fields = ["name", "email", "message"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"

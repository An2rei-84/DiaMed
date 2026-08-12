"""Админка users приложения."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Appointment, DiagnosticResult


class UserProfileInline(admin.StackedInline):
    """Inline редактирование профиля."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'


class UserAdmin(BaseUserAdmin):
    """Расширенная админка пользователя."""

    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Админка для записей на приём."""

    list_display = ['user', 'service', 'date', 'time', 'status']
    list_filter = ['status', 'date', 'service__category']
    search_fields = ['user__username', 'user__email', 'service__name', 'notes']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DiagnosticResult)
class DiagnosticResultAdmin(admin.ModelAdmin):
    """Админка для результатов диагностики."""

    list_display = ['appointment', 'doctor', 'result_date', 'is_normal']
    list_filter = ['is_normal', 'result_date', 'appointment__service__category']
    search_fields = ['appointment__user__username', 'doctor', 'conclusion']
    date_hierarchy = 'result_date'
    readonly_fields = ['result_date']


# Расширение стандартной админки
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

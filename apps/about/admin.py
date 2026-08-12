"""Админка about приложения."""

from django.contrib import admin
from .models import CompanyHistory, TeamMember, CompanyValue


@admin.register(CompanyHistory)
class CompanyHistoryAdmin(admin.ModelAdmin):
    """Админка для истории компании."""

    list_display = ['year', 'title']
    list_filter = ['year']
    search_fields = ['title', 'description']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Админка для сотрудников."""

    list_display = ['name', 'position', 'speciality', 'experience', 'is_active']
    list_filter = ['is_active', 'position']
    search_fields = ['name', 'position', 'speciality']


@admin.register(CompanyValue)
class CompanyValueAdmin(admin.ModelAdmin):
    """Админка для ценностей."""

    list_display = ['title', 'icon']
    search_fields = ['title', 'description']

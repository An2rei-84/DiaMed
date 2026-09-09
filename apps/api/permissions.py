"""Права доступа для API."""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Разрешает доступ к объекту только его владельцу (поле user)."""

    def has_object_permission(self, request, view, obj):
        """Проверяет, что объект принадлежит текущему пользователю."""
        return obj.user_id == request.user.id

"""Бизнес-логика API: расчёт свободных слотов записи.

Реализация живёт в apps.users.services — домене записей; здесь реэкспорт
для совместимости с существующими импортами API.
"""

from apps.users.services import get_available_slots  # noqa: F401

__all__ = ("get_available_slots",)

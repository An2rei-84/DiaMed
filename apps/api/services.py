"""Бизнес-логика API: расчёт свободных слотов записи.

Реализация живёт в apps.users.services — домене записей; здесь реэкспорт
для совместимости с существующими импортами API.
"""

from apps.users.services import SLOT_TAKEN_MESSAGE, get_available_slots  # noqa: F401

__all__ = ("SLOT_TAKEN_MESSAGE", "get_available_slots")

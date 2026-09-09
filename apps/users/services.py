"""Бизнес-логика записей: расчёт свободных слотов."""

from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Appointment

# Рабочие часы центра: с 8:00 до 20:00, шаг записи — 30 минут
WORKDAY_START = time(8, 0)
WORKDAY_END = time(20, 0)
SLOT_STEP = timedelta(minutes=30)

# Статусы записи, при которых время считается занятым
BUSY_STATUSES = ("pending", "confirmed")


def get_available_slots(service, date, now=None):
    """Возвращает свободные временные слоты для услуги на дату.

    Слоты, уже прошедшие сегодня, не предлагаются.

    Args:
        service: услуга, на которую записывается пациент.
        date: дата приёма.
        now: текущий момент для проверки (для тестов); по умолчанию — сейчас.

    Returns:
        list[str]: свободные слоты в формате "HH:MM" по возрастанию.
    """
    current_moment = now or timezone.localtime()
    busy = set(Appointment.objects.filter(service=service, date=date, status__in=BUSY_STATUSES).values_list("time", flat=True))

    slots = []
    current = datetime.combine(date, WORKDAY_START)
    end = datetime.combine(date, WORKDAY_END)
    while current < end:
        slot_time = current.time()
        is_past = current_moment.date() == date and slot_time <= current_moment.time()
        if slot_time not in busy and not is_past:
            slots.append(slot_time.strftime("%H:%M"))
        current += SLOT_STEP
    return slots

"""Тесты расчёта свободных слотов и эндпоинта available-slots."""

from datetime import date, datetime, time, timedelta

from django.utils import timezone

import pytest

from apps.api.services import get_available_slots
from apps.users.models import Appointment

SLOTS_URL = "/api/appointments/available-slots/"
API_LIST = "/api/appointments/"


@pytest.mark.django_db
class TestGetAvailableSlots:
    """Юнит-тесты функции get_available_slots."""

    def test_full_day_free(self, sample_service):
        """Свободный день: 24 слота с 8:00 до 19:30."""
        future = date.today() + timedelta(days=1)

        slots = get_available_slots(sample_service, future)

        assert slots[0] == "08:00"
        assert slots[-1] == "19:30"
        assert len(slots) == 24

    def test_busy_slot_excluded(self, sample_service, user, tomorrow):
        """Занятый слот (pending) не предлагается."""
        Appointment.objects.create(user=user, service=sample_service, date=tomorrow, time=time(10, 0))

        slots = get_available_slots(sample_service, tomorrow)

        assert "10:00" not in slots
        assert "09:30" in slots

    def test_past_slots_excluded_today(self, sample_service):
        """Слоты, уже прошедшие сегодня, не предлагаются."""
        today = timezone.localdate()
        now = datetime.combine(today, time(10, 30))

        slots = get_available_slots(sample_service, today, now=now)

        assert slots[0] == "11:00"
        assert "10:00" not in slots
        assert "10:30" not in slots
        assert "11:30" in slots

    def test_tomorrow_slots_not_affected_by_now(self, sample_service):
        """Фильтр прошедшего времени действует только на сегодняшнюю дату."""
        tomorrow = timezone.localdate() + timedelta(days=1)
        late_today = datetime.combine(timezone.localdate(), time(23, 59))

        slots = get_available_slots(sample_service, tomorrow, now=late_today)

        assert slots[0] == "08:00"
        assert len(slots) == 24

    def test_cancelled_appointment_does_not_block(self, sample_service, user, tomorrow):
        """Отменённая запись не занимает слот."""
        Appointment.objects.create(
            user=user,
            service=sample_service,
            date=tomorrow,
            time=time(10, 0),
            status="cancelled",
        )

        slots = get_available_slots(sample_service, tomorrow)

        assert "10:00" in slots

    def test_slots_scoped_to_service(self, sample_service, user, tomorrow):
        """Занятость другой услуги не влияет на слоты."""
        Appointment.objects.create(user=user, service=sample_service, date=tomorrow, time=time(10, 0))
        other_service = sample_service
        other_service.pk = None
        other_service.slug = "drugaya"
        other_service.save()

        slots = get_available_slots(other_service, tomorrow)

        assert "10:00" in slots


@pytest.mark.django_db
class TestAvailableSlotsAPI:
    """Тесты эндпоинта GET /api/appointments/available-slots/."""

    def test_missing_params(self, api_client):
        """Без параметров возвращается 400."""
        response = api_client.get(SLOTS_URL)

        assert response.status_code == 400
        assert "service" in response.data["detail"]

    def test_unknown_service(self, api_client, tomorrow):
        """Неизвестная услуга — 404."""
        response = api_client.get(SLOTS_URL, {"service": "net-takoy", "date": str(tomorrow)})

        assert response.status_code == 404

    def test_bad_date_format(self, api_client, sample_service):
        """Некорректный формат даты — 400."""
        response = api_client.get(SLOTS_URL, {"service": "analiz-krovi", "date": "01.02.2030"})

        assert response.status_code == 400

    def test_slots_exclude_busy(self, api_client, sample_service, user, tomorrow):
        """Эндпоинт не предлагает занятое время."""
        Appointment.objects.create(user=user, service=sample_service, date=tomorrow, time=time(10, 0))

        response = api_client.get(SLOTS_URL, {"service": "analiz-krovi", "date": str(tomorrow)})

        assert response.status_code == 200
        assert response.data["service"] == "analiz-krovi"
        assert "10:00" not in response.data["available_slots"]
        assert "11:00" in response.data["available_slots"]

    def test_create_for_past_time_today_rejected(self, auth_api_client, sample_service):
        """Запись на сегодняшнее прошедшее время отклоняется API."""
        now = timezone.localtime()
        if now.time() < time(9, 0):
            pytest.skip("тест запущен до 09:00 — прошедших слотов сегодня ещё нет")

        response = auth_api_client.post(
            API_LIST,
            {"service": sample_service.pk, "date": str(timezone.localdate()), "time": "08:00"},
            format="json",
        )

        assert response.status_code == 400

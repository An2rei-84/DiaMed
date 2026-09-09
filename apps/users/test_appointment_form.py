"""Тесты валидации слотов в форме записи на приём."""

from datetime import date, datetime, time, timedelta

import pytest

import apps.users.services as slots_module
from apps.users.forms import AppointmentForm
from apps.users.models import Appointment


def submit_form(service_pk, appointment_date, appointment_time):
    """Заполняет форму записи типовыми данными."""
    return AppointmentForm(
        data={
            "service": service_pk,
            "date": appointment_date.isoformat(),
            "time": appointment_time,
            "notes": "",
        }
    )


@pytest.fixture
def fixed_noon(monkeypatch, tomorrow):
    """Фиксирует «сейчас» на 12:00 для детерминированных тестов формы."""
    moment = datetime.combine(tomorrow, time(12, 0))
    original = slots_module.get_available_slots
    monkeypatch.setattr(
        slots_module,
        "get_available_slots",
        lambda service, day, now=None: original(service, day, now=moment),
    )
    return moment


@pytest.mark.django_db
class TestAppointmentFormSlots:
    """Проверка слотов через веб-форму записи."""

    def test_valid_slot_passes(self, user, sample_service, fixed_noon):
        """Свободное будущее время проходит валидацию."""
        form = submit_form(sample_service.pk, date.today() + timedelta(days=2), "10:00")

        assert form.is_valid(), form.errors

    def test_busy_slot_rejected(self, user, sample_service, tomorrow, fixed_noon):
        """Занятое время отклоняется с внятной ошибкой."""
        Appointment.objects.create(user=user, service=sample_service, date=tomorrow, time=time(10, 0))

        form = submit_form(sample_service.pk, tomorrow, "10:00")

        assert not form.is_valid()
        assert "занято" in str(form.errors)

    def test_past_time_today_rejected(self, user, sample_service, monkeypatch):
        """Время, которое уже прошло сегодня, отклоняется формой."""
        today = date.today()
        moment = datetime.combine(today, time(12, 0))
        original = slots_module.get_available_slots
        monkeypatch.setattr(
            slots_module,
            "get_available_slots",
            lambda service, day, now=None: original(service, day, now=moment),
        )

        form = submit_form(sample_service.pk, today, "08:00")

        assert not form.is_valid()
        assert "прошло" in str(form.errors)

    def test_out_of_work_hours_rejected(self, user, sample_service, tomorrow, fixed_noon):
        """Время вне рабочих часов отклоняется формой."""
        form = submit_form(sample_service.pk, tomorrow, "23:30")

        assert not form.is_valid()
        assert "рабочих часов" in str(form.errors)

    def test_past_date_still_rejected(self, user, sample_service):
        """Прошедшая дата по-прежнему отклоняется (полевая валидация)."""
        form = submit_form(sample_service.pk, date(2020, 1, 1), "10:00")

        assert not form.is_valid()
        assert "прошедшую дату" in str(form.errors)

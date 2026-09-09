"""Тесты Celery-задач приложения users."""

from datetime import time

import pytest

from apps.users.models import Appointment
from apps.users.tasks import send_appointment_confirmation, send_appointment_reminders


def make_appointment(user, service, date_value, time_value=time(10, 0), status="pending"):
    """Создаёт запись на приём с заданными параметрами."""
    return Appointment.objects.create(user=user, service=service, date=date_value, time=time_value, status=status)


@pytest.mark.django_db
class TestAppointmentConfirmationTask:
    """Задача отправки подтверждения о записи."""

    def test_email_sent_to_patient(self, user, sample_service, tomorrow, mailoutbox):
        """Письмо-подтверждение приходит на email пациента."""
        appointment = make_appointment(user, sample_service, tomorrow)

        result = send_appointment_confirmation(appointment.pk)

        assert user.email in result
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == [user.email]
        assert sample_service.name in mailoutbox[0].subject

    def test_missing_appointment_raises(self, user, sample_service):
        """Несуществующий идентификатор записи вызывает ошибку."""
        with pytest.raises(Appointment.DoesNotExist):
            send_appointment_confirmation(9999)


@pytest.mark.django_db
class TestAppointmentRemindersTask:
    """Задача ежедневных напоминаний о приёмах."""

    def test_reminder_sent_for_tomorrow(self, user, sample_service, tomorrow, mailoutbox):
        """Пациенту с приёмом на завтра отправляется напоминание."""
        make_appointment(user, sample_service, tomorrow)

        result = send_appointment_reminders()

        assert "1" in result
        assert len(mailoutbox) == 1
        assert "Напоминание" in mailoutbox[0].subject

    def test_cancelled_appointment_skipped(self, user, sample_service, tomorrow, mailoutbox):
        """Отменённые записи не получают напоминаний."""
        make_appointment(user, sample_service, tomorrow, status="cancelled")

        send_appointment_reminders()

        assert len(mailoutbox) == 0

    def test_no_appointments_no_emails(self, db, mailoutbox):
        """Если приёмов на завтра нет — писем не отправляется."""
        result = send_appointment_reminders()

        assert "0" in result
        assert len(mailoutbox) == 0

"""Celery-задачи приложения users."""

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from celery import shared_task

from .models import Appointment


@shared_task
def send_appointment_confirmation(appointment_id):
    """Отправляет письмо-подтверждение после создания записи на приём.

    Args:
        appointment_id: идентификатор записи.

    Returns:
        str: отчёт об отправке.
    """
    appointment = Appointment.objects.select_related("user", "service").get(pk=appointment_id)
    send_mail(
        subject=f"Запись на «{appointment.service.name}» создана",
        message=(
            f"Здравствуйте, {appointment.user.get_full_name() or appointment.user.username}!\n\n"
            f"Вы записаны на услугу «{appointment.service.name}»:\n"
            f"Дата: {appointment.date.strftime('%d.%m.%Y')}\n"
            f"Время: {appointment.time.strftime('%H:%M')}\n\n"
            "Статус записи: ожидает подтверждения. Мы свяжемся с вами для уточнения деталей."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[appointment.user.email],
    )
    return f"Подтверждение отправлено на {appointment.user.email}"


@shared_task
def send_appointment_reminders():
    """Напоминает пациентам о приёмах, назначенных на завтра.

    Запускается по расписанию (Celery Beat, ежедневно в 18:00).

    Returns:
        str: количество отправленных напоминаний.
    """
    tomorrow = timezone.localdate() + timedelta(days=1)
    appointments = Appointment.objects.filter(date=tomorrow, status__in=("pending", "confirmed")).select_related(
        "user", "service"
    )

    for appointment in appointments:
        send_mail(
            subject=f"Напоминание: «{appointment.service.name}» завтра",
            message=(
                f"Здравствуйте, {appointment.user.get_full_name() or appointment.user.username}!\n\n"
                f"Напоминаем о вашем приёме:\n"
                f"Услуга: {appointment.service.name}\n"
                f"Дата: {appointment.date.strftime('%d.%m.%Y')}\n"
                f"Время: {appointment.time.strftime('%H:%M')}\n\n"
                "Не забудьте подготовку к процедуре — подробности на сайте."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.user.email],
        )
    return f"Отправлено напоминаний: {appointments.count()}"

"""Команда засеивания демо-данных для QA-автотестов (E2E и API)."""

from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.services.models import Service, ServiceCategory
from apps.users.models import Appointment, DiagnosticResult

QA_USERNAME = "qa_api"
QA_PASSWORD = "qa_pass_123"
QA2_USERNAME = "qa_api2"
QA2_PASSWORD = "qa_pass_456"


class Command(BaseCommand):
    """Создаёт минимальный набор данных для автотестов."""

    help = "Засеивает демо-данные для автотестов: категория, услуга, тестовый пользователь (идемпотентно)"

    def handle(self, *args, **options):
        """Создаёт объекты, если их ещё нет; пароль тестового пользователя обновляет всегда."""
        category, _ = ServiceCategory.objects.get_or_create(
            slug="diagnostika",
            defaults={
                "name": "Диагностика",
                "description": "Диагностические услуги",
                "icon": "bi-activity",
            },
        )
        service, _ = Service.objects.get_or_create(
            slug="analiz-krovi",
            defaults={
                "name": "Анализ крови",
                "category": category,
                "description": "Общий анализ крови: гемоглобин, эритроциты, лейкоциты и другие показатели.",
                "price": 1500.00,
                "duration": 30,
                "preparation": "Не есть за 4 часа до анализа",
                "is_active": True,
            },
        )
        user, created = User.objects.get_or_create(
            username=QA_USERNAME,
            defaults={"email": "qa_api@example.com", "first_name": "Кью", "last_name": "Эйпиай"},
        )
        user.set_password(QA_PASSWORD)
        user.save()

        second_user, _ = User.objects.get_or_create(
            username=QA2_USERNAME,
            defaults={"email": "qa_api2@example.com", "first_name": "Второй", "last_name": "Тестовый"},
        )
        second_user.set_password(QA2_PASSWORD)
        second_user.save()

        inactive_service, _ = Service.objects.get_or_create(
            slug="otklyuchena",
            defaults={
                "name": "Услуга отключена",
                "category": category,
                "description": "Временно недоступна — для негативных проверок.",
                "price": 500.00,
                "is_active": False,
            },
        )
        ecg_service, _ = Service.objects.get_or_create(
            slug="ekg-serdca",
            defaults={
                "name": "ЭКГ сердца",
                "category": category,
                "description": "Электрокардиография: регистрация электрической активности сердца.",
                "price": 900.00,
                "duration": 20,
                "is_active": True,
            },
        )

        # Прошлые брони демо-пользователя не нужны: каждый прогон E2E начинается с чистого листа
        removed, _ = Appointment.objects.filter(user=user).delete()

        completed = Appointment.objects.create(
            user=user,
            service=service,
            date=date.today() - timedelta(days=1),
            time=time(9, 0),
            status="completed",
        )
        DiagnosticResult.objects.get_or_create(
            appointment=completed,
            defaults={
                "conclusion": "Показатели в пределах нормы",
                "recommendations": "Повторить анализ через год",
                "doctor": "Иванов И. И.",
                "is_normal": True,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Демо-данные готовы: услуги «{service.name}», «{ecg_service.name}», «{inactive_service.name}», "
                f"пользователи {QA_USERNAME}/{QA2_USERNAME} (создан: {created}), "
                f"удалено прошлых броней: {removed}, завершённая запись с результатом: есть"
            )
        )

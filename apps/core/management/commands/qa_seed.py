"""Команда засеивания демо-данных для QA-автотестов (E2E и API)."""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.services.models import Service, ServiceCategory
from apps.users.models import Appointment

QA_USERNAME = "qa_api"
QA_PASSWORD = "qa_pass_123"


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

        # Прошлые брони демо-пользователя не нужны: каждый прогон E2E начинается с чистого листа
        removed, _ = Appointment.objects.filter(user=user).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Демо-данные готовы: услуга «{service.name}», "
                f"пользователь {QA_USERNAME} (создан: {created}), удалено прошлых броней: {removed}"
            )
        )

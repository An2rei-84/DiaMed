"""Фикстуры для тестов REST API."""

from datetime import time

import pytest
from rest_framework.test import APIClient

from apps.services.models import Service
from apps.users.models import Appointment, DiagnosticResult


@pytest.fixture(autouse=True)
def _clear_cache():
    """Очищает кэш перед каждым тестом (в API есть cache_page)."""

    from django.core.cache import cache

    cache.clear()


@pytest.fixture
def api_client():
    """APIClient без аутентификации."""
    return APIClient()


@pytest.fixture
def auth_api_client(api_client, user):
    """APIClient, аутентифицированный под обычным пользователем."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def appointment(db, user, sample_service, tomorrow):
    """Тестовая запись на приём (завтра в 10:00)."""
    return Appointment.objects.create(
        user=user,
        service=sample_service,
        date=tomorrow,
        time=time(10, 0),
        status="pending",
    )


@pytest.fixture
def other_user(db, user_data):
    """Второй пользователь (не владелец тестовой записи)."""

    from django.contrib.auth.models import User

    return User.objects.create_user(username="other", email="other@example.com", password="otherpass123")


@pytest.fixture
def inactive_service(db, sample_service_category):
    """Неактивная услуга."""
    return Service.objects.create(
        name="Услуга отключена",
        slug="otklyuchena",
        category=sample_service_category,
        description="Временно недоступна",
        price=100.00,
        is_active=False,
    )


@pytest.fixture
def diagnostic_result(db, appointment):
    """Готовый результат диагностики по тестовой записи."""
    return DiagnosticResult.objects.create(
        appointment=appointment,
        conclusion="Показатели в пределах нормы",
        recommendations="Повторить анализ через год",
        doctor="Иванов И. И.",
        is_normal=True,
    )

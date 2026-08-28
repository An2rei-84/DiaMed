"""Общие фикстуры для тестов проекта."""

from django.contrib.auth.models import User

import pytest


@pytest.fixture
def user_data():
    """Данные для создания тестового пользователя."""
    return {
        "username": "testuser",
        "first_name": "Тест",
        "last_name": "Тестов",
        "email": "test@example.com",
        "password": "testpass123",
    }


@pytest.fixture
def user(db, user_data):
    """Создаёт тестового пользователя."""
    user = User.objects.create_user(
        username=user_data["username"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        email=user_data["email"],
        password=user_data["password"],
    )
    return user


@pytest.fixture
def authenticated_client(db, client, user):
    """Создаёт аутентифицированный клиент."""
    client.force_login(user)
    return client


@pytest.fixture
def admin_user(db):
    """Создаёт пользователя с правами администратора."""
    admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="admin123")
    return admin


@pytest.fixture
def admin_client(db, client, admin_user):
    """Создаёт клиент с правами администратора."""
    client.force_login(admin_user)
    return client


@pytest.fixture
def sample_service_category(db):
    """Создаёт тестовую категорию услуг."""
    from apps.services.models import ServiceCategory

    category = ServiceCategory.objects.create(
        name="Диагностика", slug="diagnostika", description="Диагностические услуги", icon="bi-activity"
    )
    return category


@pytest.fixture
def sample_service(db, sample_service_category):
    """Создаёт тестовую услугу."""
    from apps.services.models import Service

    service = Service.objects.create(
        name="Анализ крови",
        slug="analiz-krovi",
        category=sample_service_category,
        description="Общий анализ крови",
        price=1500.00,
        duration=30,
        preparation="Не есть за 4 часа до анализа",
        is_active=True,
    )
    return service


@pytest.fixture
def sample_contact(db):
    """Создаёт тестовые контакты."""
    from apps.contacts.models import Contact

    contact = Contact.objects.create(
        address="г. Москва, ул. Примерная, д. 1",
        phone="+7 (495) 123-45-67",
        email="info@diamed.ru",
        working_hours="Пн-Пт: 8:00-20:00\nСб: 9:00-18:00",
        map_url="https://maps.google.com/?q=Москва",
    )
    return contact

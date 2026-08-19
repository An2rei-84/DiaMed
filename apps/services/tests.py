"""Тесты для services приложения."""

from django.urls import reverse

import pytest

from apps.services.models import Service, ServiceCategory


@pytest.mark.django_db
class TestServiceCategoryModel:
    """Тесты модели ServiceCategory."""

    def test_create_service_category(self):
        """Тест создания категории услуг."""
        category = ServiceCategory.objects.create(name="Диагностика", slug="diagnostika", description="Диагностические услуги")
        assert category.name == "Диагностика"
        assert category.slug == "diagnostika"
        assert category.description == "Диагностические услуги"

    def test_service_category_str(self):
        """Тест строкового представления."""
        category = ServiceCategory.objects.create(name="Анализы", slug="analizy")
        assert str(category) == "Анализы"

    def test_service_category_unique_slug(self, db):
        """Тест уникальности slug."""
        ServiceCategory.objects.create(name="Терапия", slug="terapia")
        # Попытка создать дубликат
        with pytest.raises(Exception):  # IntegrityError
            ServiceCategory.objects.create(name="Терапия 2", slug="terapia")

    def test_service_category_ordering(self, db):
        """Тест сортировки категорий."""
        ServiceCategory.objects.create(name="Б", slug="b")
        ServiceCategory.objects.create(name="А", slug="a")
        ServiceCategory.objects.create(name="В", slug="v")
        categories = list(ServiceCategory.objects.all())
        assert categories[0].name == "А"
        assert categories[1].name == "Б"
        assert categories[2].name == "В"


@pytest.mark.django_db
class TestServiceModel:
    """Тесты модели Service."""

    def test_create_service(self, sample_service_category):
        """Тест создания услуги."""
        service = Service.objects.create(
            name="МРТ головного мозга",
            slug="mrt-golovnogo-mozga",
            category=sample_service_category,
            description="Магнитно-резонансная томография",
            price=5000.00,
            duration=45,
            preparation="Без металлических изделий",
        )
        assert service.name == "МРТ головного мозга"
        assert service.price == 5000.00
        assert service.duration == 45
        assert service.is_active is True

    def test_service_str(self, sample_service_category):
        """Тест строкового представления."""
        service = Service.objects.create(
            name="УЗИ", slug="uzi", category=sample_service_category, description="Ультразвуковое исследование", price=2000.00
        )
        str_repr = str(service)
        assert "УЗИ" in str_repr
        assert "2000.00" in str_repr
        assert "₽" in str_repr

    def test_service_unique_slug(self, sample_service_category):
        """Тест уникальности slug услуги."""
        Service.objects.create(
            name="Услуга", slug="usluga", category=sample_service_category, description="Описание", price=1000.00
        )
        # Попытка создать дубликат
        with pytest.raises(Exception):
            Service.objects.create(
                name="Услуга 2", slug="usluga", category=sample_service_category, description="Описание 2", price=2000.00
            )

    def test_service_ordering(self, sample_service_category):
        """Тест сортировки услуг."""
        Service.objects.create(name="Б", slug="b", category=sample_service_category, description="Описание", price=1000.00)
        Service.objects.create(name="А", slug="a", category=sample_service_category, description="Описание", price=1000.00)
        services = list(Service.objects.all())
        # Должны быть отсортированы по category, name
        assert services[0].name == "А"
        assert services[1].name == "Б"

    def test_service_active_filter(self, sample_service_category):
        """Тест фильтрации активных услуг."""
        Service.objects.create(
            name="Активная услуга",
            slug="active",
            category=sample_service_category,
            description="Описание",
            price=1000.00,
            is_active=True,
        )
        Service.objects.create(
            name="Неактивная услуга",
            slug="inactive",
            category=sample_service_category,
            description="Описание",
            price=2000.00,
            is_active=False,
        )
        active_services = Service.objects.filter(is_active=True)
        assert active_services.count() == 1
        assert active_services.first().name == "Активная услуга"

    def test_service_category_relation(self, sample_service_category):
        """Тест связи с категорией."""
        service = Service.objects.create(
            name="Услуга", slug="usluga", category=sample_service_category, description="Описание", price=1000.00
        )
        assert service.category.name == "Диагностика"
        assert sample_service_category.services.count() == 1
        assert sample_service_category.services.first() == service


@pytest.mark.django_db
class TestServicesViews:
    """Тесты views services приложения."""

    def test_services_list_view(self, client, sample_service):
        """Тест страницы списка услуг."""
        response = client.get(reverse("services:list"))
        assert response.status_code == 200
        assert "services" in response.context
        assert "categories" in response.context

    def test_services_list_with_category_filter(self, client, sample_service, sample_service_category):
        """Тест фильтрации услуг по категории."""
        # Создаем еще одну категорию и услугу
        category2 = ServiceCategory.objects.create(name="Лечение", slug="lechenie")
        Service.objects.create(
            name="Консультация", slug="konsultacia", category=category2, description="Описание", price=3000.00, is_active=True
        )

        response = client.get(reverse("services:list"), {"category": "diagnostika"})
        assert response.status_code == 200
        assert len(response.context["services"]) == 1
        assert response.context["services"][0].name == "Анализ крови"

    def test_service_detail_view(self, client, sample_service):
        """Тест детальной страницы услуги."""
        response = client.get(reverse("services:detail", kwargs={"slug": "analiz-krovi"}))
        assert response.status_code == 200
        assert "service" in response.context
        assert response.context["service"].name == "Анализ крови"

    def test_service_detail_not_found(self, client):
        """Тест детальной страницы с несуществующим slug."""
        response = client.get(reverse("services:detail", kwargs={"slug": "not-exist"}))
        assert response.status_code == 404

    def test_service_detail_inactive_service(self, sample_service_category):
        """Тест что неактивная услуга не доступна."""
        # Создаем неактивную услугу
        Service.objects.create(
            name="Неактивная услуга",
            slug="inactive-service",
            category=sample_service_category,
            description="Описание",
            price=1000.00,
            is_active=False,
        )
        from django.test import Client

        client = Client()
        response = client.get(reverse("services:detail", kwargs={"slug": "inactive-service"}))
        assert response.status_code == 404


@pytest.mark.django_db
class TestServicesUrls:
    """Тесты URL routing services приложения."""

    def test_services_list_url_resolves(self):
        """Тест разрешения URL списка услуг."""
        url = reverse("services:list")
        assert url == "/services/"

    def test_service_detail_url_resolves(self):
        """Тест разрешения URL детальной страницы."""
        url = reverse("services:detail", kwargs={"slug": "test-slug"})
        assert url == "/services/test-slug/"

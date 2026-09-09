"""Тесты API услуг и категорий."""

from django.urls import reverse

import pytest


@pytest.mark.django_db
class TestServiceCategoryAPI:
    """Тесты эндпоинта /api/categories/."""

    def test_list_categories_anonymous(self, api_client, sample_service_category):
        """Анонимный пользователь видит список категорий."""
        response = api_client.get("/api/categories/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["slug"] == "diagnostika"

    def test_category_fields(self, api_client, sample_service_category):
        """В ответе присутствуют все поля категории."""
        response = api_client.get("/api/categories/")

        category = response.data[0]
        assert set(category.keys()) == {"id", "name", "slug", "description", "icon"}


@pytest.mark.django_db
class TestServiceAPI:
    """Тесты эндпоинта /api/services/."""

    def test_list_services_anonymous(self, api_client, sample_service):
        """Анонимный пользователь видит список активных услуг."""
        response = api_client.get("/api/services/")

        assert response.status_code == 200
        slugs = [item["slug"] for item in response.data["results"]]
        assert "analiz-krovi" in slugs

    def test_inactive_service_hidden(self, api_client, sample_service, inactive_service):
        """Неактивные услуги не попадают в список."""
        response = api_client.get("/api/services/")

        slugs = [item["slug"] for item in response.data["results"]]
        assert "otklyuchena" not in slugs

    def test_filter_by_category(self, api_client, sample_service, inactive_service):
        """Фильтр по категории отбирает только её услуги."""
        response = api_client.get("/api/services/", {"category__slug": "diagnostika"})

        assert response.status_code == 200
        assert all(item["category_slug"] == "diagnostika" for item in response.data["results"])

    def test_search(self, api_client, sample_service):
        """Поиск по названию услуги."""
        response = api_client.get("/api/services/", {"search": "крови"})

        assert response.status_code == 200
        assert "analiz-krovi" in [item["slug"] for item in response.data["results"]]

    def test_ordering_by_price(self, api_client, sample_service, inactive_service):
        """Сортировка по цене."""
        response = api_client.get("/api/services/", {"ordering": "price"})

        prices = [item["price"] for item in response.data["results"]]
        assert prices == sorted(prices)

    def test_detail_by_slug(self, api_client, sample_service):
        """Детальная информация об услуге по slug."""
        response = api_client.get("/api/services/analiz-krovi/")

        assert response.status_code == 200
        assert response.data["name"] == "Анализ крови"
        assert response.data["category"] == "Диагностика"
        assert response.data["duration"] == 30

    def test_detail_not_found(self, api_client):
        """Несуществующая услуга возвращает 404."""
        response = api_client.get("/api/services/net-takoy/")

        assert response.status_code == 404

    def test_list_is_cached(self, api_client, sample_service, django_assert_num_queries):
        """Повторный запрос списка выполняется без обращений к БД (кэш)."""
        api_client.get("/api/services/")

        with django_assert_num_queries(0):
            response = api_client.get("/api/services/")

        assert response.status_code == 200

    def test_reverse_url(self):
        """URL услуг доступен по имени маршрута."""
        assert reverse("service-list") == "/api/services/"

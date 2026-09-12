"""Black-box тесты каталога: категории и услуги (/api/categories/, /api/services/)."""

import requests


class TestCategoriesAPI:
    """Публичный каталог категорий."""

    def test_list_anonymous_allowed(self, base_url):
        """Категории доступны анонимно и отдаются без пагинации."""
        response = requests.get(f"{base_url}/api/categories/", timeout=10)

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert any(item["slug"] == "diagnostika" for item in body)


class TestServicesAPI:
    """Публичный каталог услуг с фильтрами, поиском и сортировкой."""

    def test_list_paginated(self, base_url):
        """Список услуг в формате пагинации DRF."""
        response = requests.get(f"{base_url}/api/services/", timeout=10)

        assert response.status_code == 200
        body = response.json()
        assert {"count", "next", "previous", "results"} <= set(body)
        assert body["count"] >= 1

    def test_list_contains_seeded_service(self, base_url):
        """Демо-услуга присутствует в списке с категорией."""
        response = requests.get(f"{base_url}/api/services/", timeout=10)

        items = [item for item in response.json()["results"] if item["slug"] == "analiz-krovi"]
        assert items, "Демо-услуга analiz-krovi не найдена в списке"
        assert items[0]["category_slug"] == "diagnostika"
        assert items[0]["price"] == "1500.00"

    def test_search_filters_results(self, base_url):
        """Поиск по подстроке названия."""
        found = requests.get(f"{base_url}/api/services/", params={"search": "крови"}, timeout=10).json()
        empty = requests.get(f"{base_url}/api/services/", params={"search": "абракадабра"}, timeout=10).json()

        assert found["count"] >= 1
        assert empty["count"] == 0

    def test_filter_by_category_slug(self, base_url):
        """Фильтр по категории и пустой результат для неизвестной."""
        by_category = requests.get(f"{base_url}/api/services/", params={"category__slug": "diagnostika"}, timeout=10).json()
        unknown = requests.get(f"{base_url}/api/services/", params={"category__slug": "нет-такой"}, timeout=10).json()

        assert by_category["count"] >= 1
        assert all(item["category_slug"] == "diagnostika" for item in by_category["results"])
        assert unknown["count"] == 0

    def test_ordering_by_price(self, base_url):
        """Сортировка по цене: первая позиция не дороже второй."""
        response = requests.get(f"{base_url}/api/services/", params={"ordering": "price"}, timeout=10)

        prices = [float(item["price"]) for item in response.json()["results"]]
        assert len(prices) >= 2
        assert prices[0] <= prices[1]

    def test_inactive_service_hidden(self, base_url):
        """Неактивная услуга не видна в каталоге."""
        response = requests.get(f"{base_url}/api/services/", params={"search": "отключена"}, timeout=10)

        assert response.json()["count"] == 0

    def test_detail_by_slug(self, base_url):
        """Детальная карточка услуги по slug."""
        response = requests.get(f"{base_url}/api/services/analiz-krovi/", timeout=10)

        assert response.status_code == 200
        assert response.json()["name"] == "Анализ крови"
        assert response.json()["duration"] == 30

    def test_detail_unknown_slug_404(self, base_url):
        """Неизвестный slug — 404."""
        response = requests.get(f"{base_url}/api/services/net-takoy-uslugi/", timeout=10)

        assert response.status_code == 404

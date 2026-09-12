"""Смок-тесты: ключевые страницы открываются и показывают ожидаемое."""

from pages.dashboard_page import DashboardPage


class TestSmoke:
    """Проверка работоспособности основных страниц."""

    def test_home_page_opens(self, page, base_url):
        """Главная страница открывается с заголовком DiaMed."""
        page.goto(base_url + "/")

        assert "DiaMed" in page.title()

    def test_favicon_link_present(self, page, base_url):
        """Фавиконка подключена в head каждой страницы."""
        page.goto(base_url + "/")

        assert page.locator('link[rel="icon"]').count() >= 1

    def test_services_list_shows_seeded_service(self, page, base_url):
        """В списке услуг отображается услуга из демо-данных."""
        page.goto(base_url + "/services/")

        assert page.get_by_text("Анализ крови").first.is_visible()

    def test_service_detail_opens(self, page, base_url):
        """Страница услуги открывается и показывает описание."""
        page.goto(base_url + "/services/analiz-krovi/")

        assert page.get_by_text("Общий анализ крови").first.is_visible()

    def test_api_docs_opens(self, page, base_url):
        """Swagger UI API-документации открывается."""
        page.goto(base_url + "/api/docs/")

        assert "DiaMed API" in page.title()

    def test_anonymous_redirects_to_login_from_dashboard(self, page, base_url):
        """Анонимного посетителя личный кабинет перенаправляет на вход."""
        DashboardPage(page, base_url).open("/users/dashboard/")

        assert "/users/login/" in page.url

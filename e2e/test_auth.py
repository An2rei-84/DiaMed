"""E2E-тесты регистрации, входа и выхода."""

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from pages.register_page import RegisterPage

QA_USERNAME = "qa_api"
QA_PASSWORD = "qa_pass_123"


class TestRegister:
    """Регистрация нового пациента через веб-интерфейс."""

    def test_register_success_and_logged_in(self, page, base_url, unique_suffix):
        """После успешной регистрации пользователь сразу залогинен."""
        register = RegisterPage(page, base_url)
        register.register(
            username=f"e2e_user_{unique_suffix}",
            first_name="Иван",
            last_name="Тестов",
            email=f"e2e_user_{unique_suffix}@example.com",
            password="e2ePass_123",
        )

        assert register.is_logged_in()
        assert "Регистрация успешна" in register.alert_text()

    def test_register_password_mismatch_shows_error(self, page, base_url, unique_suffix):
        """Несовпадающие пароли отклоняются с ошибкой под полем."""
        register = RegisterPage(page, base_url)
        register.register_mismatched_passwords(
            username=f"e2e_user_{unique_suffix}",
            first_name="Иван",
            last_name="Тестов",
            email=f"e2e_user_{unique_suffix}@example.com",
            password="e2ePass_123",
            password2="other_123",
        )

        assert register.has_field_error()


class TestLoginLogout:
    """Вход и выход из аккаунта."""

    def test_login_success_opens_dashboard(self, page, base_url):
        """Вход под демо-пользователем открывает личный кабинет."""
        dashboard = DashboardPage(page, base_url)
        LoginPage(page, base_url).login(QA_USERNAME, QA_PASSWORD)

        dashboard.expect_visible()
        assert dashboard.welcome_text()

    def test_login_wrong_password_shows_error(self, page, base_url):
        """Неверный пароль показывает сообщение об ошибке."""
        login = LoginPage(page, base_url)
        login.login(QA_USERNAME, "wrong-password")

        assert login.error_alert_visible()

    def test_logout_returns_to_public_navbar(self, page, base_url):
        """После выхода в навбаре снова появляются «Войти» и «Регистрация»."""
        dashboard = DashboardPage(page, base_url)
        LoginPage(page, base_url).login(QA_USERNAME, QA_PASSWORD)
        dashboard.expect_visible()

        dashboard.logout()

        assert not dashboard.is_logged_in()

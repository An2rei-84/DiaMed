"""Page object страницы входа."""

from .base_page import BasePage


class LoginPage(BasePage):
    """Вход в личный кабинет (/users/login/)."""

    def login(self, username, password):
        """Заполняет форму входа и отправляет её."""
        self.open("/users/login/")
        self.page.fill("#id_username", username)
        self.page.fill("#id_password", password)
        self.page.get_by_role("button", name="Войти").click()
        return self

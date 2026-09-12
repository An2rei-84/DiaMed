"""Page object страницы регистрации."""

from .base_page import BasePage


class RegisterPage(BasePage):
    """Регистрация нового пациента (/users/register/)."""

    def register(self, username, first_name, last_name, email, password):
        """Заполняет форму регистрации и отправляет её."""
        self.open("/users/register/")
        self.page.fill("#id_username", username)
        self.page.fill("#id_first_name", first_name)
        self.page.fill("#id_last_name", last_name)
        self.page.fill("#id_email", email)
        self.page.fill("#id_password1", password)
        self.page.fill("#id_password2", password)
        self.page.get_by_role("button", name="Зарегистрироваться").click()
        return self

    def register_mismatched_passwords(self, username, first_name, last_name, email, password, password2):
        """Отправляет форму с несовпадающими паролями."""
        self.open("/users/register/")
        self.page.fill("#id_username", username)
        self.page.fill("#id_first_name", first_name)
        self.page.fill("#id_last_name", last_name)
        self.page.fill("#id_email", email)
        self.page.fill("#id_password1", password)
        self.page.fill("#id_password2", password2)
        self.page.get_by_role("button", name="Зарегистрироваться").click()
        return self

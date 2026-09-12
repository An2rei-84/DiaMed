"""Базовый page object: общие элементы всех страниц."""

from playwright.sync_api import Page


class BasePage:
    """Обёртка над Playwright-страницей с общими элементами интерфейса."""

    def __init__(self, page: Page, base_url: str):
        """Сохраняет страницу и базовый URL приложения."""
        self.page = page
        self.base_url = base_url

    def open(self, path="/"):
        """Открывает страницу по пути относительно базового URL."""
        self.page.goto(self.base_url + path)
        return self

    # ---- Навбар ----

    def is_logged_in(self):
        """Пользователь аутентифицирован, если в навбаре есть кнопка «Выйти»."""
        return self.page.locator(".navbar").get_by_role("button", name="Выйти").is_visible()

    def logout(self):
        """Выходит из аккаунта через кнопку в навбаре."""
        self.page.locator(".navbar").get_by_role("button", name="Выйти").click()
        return self

    # ---- Сообщения и ошибки ----

    def alert_text(self):
        """Текст всплывающего сообщения (django messages), пустая строка, если его нет."""
        alert = self.page.locator(".alert").first
        return alert.text_content() or "" if alert.is_visible() else ""

    def error_alert_visible(self):
        """Показано ли сообщение об ошибке (alert-danger)."""
        return self.page.locator(".alert-danger").first.is_visible()

    def field_error(self):
        """Текст ошибки под полем формы, None, если ошибок нет."""
        error = self.page.locator(".invalid-feedback").first
        return error.text_content() or "" if error.is_visible() else None

    def has_field_error(self):
        """Показана ли ошибка валидации под каким-либо полем."""
        return self.page.locator(".invalid-feedback").first.is_visible()

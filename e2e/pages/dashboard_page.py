"""Page object личного кабинета со списком записей."""

from playwright.sync_api import expect

from .base_page import BasePage


class DashboardPage(BasePage):
    """Личный кабинет пациента (/users/dashboard/)."""

    def welcome_text(self):
        """Заголовок приветствия."""
        return self.page.get_by_role("heading").filter(has_text="Добро пожаловать").first.text_content() or ""

    def appointment_row(self, service_name):
        """Строка таблицы записей по названию услуги."""
        return self.page.locator("table tbody tr").filter(has_text=service_name).first

    def has_appointment_row(self, service_name):
        """Есть ли запись с указанной услугой в таблице."""
        return self.appointment_row(service_name).is_visible()

    def row_status(self, service_name):
        """Текст статуса (бейдж) у записи с указанной услугой, без лишних пробелов."""
        raw = self.appointment_row(service_name).locator(".badge").first.text_content() or ""
        return " ".join(raw.split())

    def cancel_appointment(self, service_name):
        """Отменяет запись по названию услуги (подтверждает браузерный диалог)."""
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.appointment_row(service_name).get_by_role("link", name="Отменить").first.click()
        return self

    def empty_state_text(self):
        """Текст заглушки, если записей нет."""
        return self.page.get_by_text("У вас пока нет записей").text_content() or ""

    def expect_visible(self):
        """Проверка, что кабинет открылся (для expect-ассертов)."""
        expect(self.page.get_by_role("heading").filter(has_text="Добро пожаловать").first).to_be_visible()

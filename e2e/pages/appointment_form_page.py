"""Page object формы записи на приём."""

from .base_page import BasePage


class AppointmentFormPage(BasePage):
    """Создание записи на приём (/users/appointment/create/)."""

    def book(self, service_name, appointment_date, appointment_time, notes=""):
        """Выбирает услугу, дату и время и отправляет форму.

        Args:
            service_name: название услуги в выпадающем списке.
            appointment_date: дата приёма (datetime.date).
            appointment_time: время слота в формате "HH:MM".
            notes: примечание к записи.
        """
        self.open("/users/appointment/create/")
        # Лейбл опции — это str(услуги) («Анализ крови - 1500.00 ₽»), поэтому
        # ищем опцию по подстроке и выбираем по value
        option_value = self.page.locator("#id_service option", has_text=service_name).first.get_attribute("value")
        self.page.select_option("#id_service", value=option_value)
        self.page.fill("#id_date", appointment_date.isoformat())
        self.page.fill("#id_time", appointment_time)
        self.page.fill("#id_notes", notes)
        self.page.get_by_role("button", name="Записаться").click()
        return self

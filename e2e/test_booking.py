"""E2E-тесты записи на приём: успех, ошибки валидации, отмена."""

from pages.appointment_form_page import AppointmentFormPage
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from pages.register_page import RegisterPage

SERVICE_NAME = "Анализ крови"
SERVICE_SLUG = "analiz-krovi"
QA_USERNAME = "qa_api"
QA_PASSWORD = "qa_pass_123"


class TestBooking:
    """Критический путь пациента: запись, ошибки, отмена."""

    def test_book_appointment_success(self, page, base_url, future_date, free_slot):
        """Свободный слот бронируется, запись появляется в кабинете со статусом «Ожидает»."""
        LoginPage(page, base_url).login(QA_USERNAME, QA_PASSWORD)
        form = AppointmentFormPage(page, base_url)
        form.book(SERVICE_NAME, future_date, free_slot)

        assert "Запись на приём создана" in form.alert_text()
        dashboard = DashboardPage(page, base_url)
        assert dashboard.has_appointment_row(SERVICE_NAME)
        assert dashboard.row_status(SERVICE_NAME) == "Ожидает"

    def test_busy_slot_rejected(self, page, base_url, future_date, free_slot):
        """Повторная запись на тот же слот отклоняется с ошибкой «занято»."""
        LoginPage(page, base_url).login(QA_USERNAME, QA_PASSWORD)
        form = AppointmentFormPage(page, base_url)
        form.book(SERVICE_NAME, future_date, free_slot)
        assert "Запись на приём создана" in form.alert_text()

        form.book(SERVICE_NAME, future_date, free_slot)

        error = form.field_error() or ""
        assert "занято" in error.lower()

    def test_out_of_work_hours_rejected(self, page, base_url, future_date):
        """Слот вне рабочих часов (23:30) отклоняется формой."""
        LoginPage(page, base_url).login(QA_USERNAME, QA_PASSWORD)
        form = AppointmentFormPage(page, base_url)
        form.book(SERVICE_NAME, future_date, "23:30")

        error = form.field_error() or ""
        assert "рабочих часов" in error

    def test_cancel_appointment(self, page, base_url, future_date, free_slot):
        """Запись можно отменить из кабинета; статус меняется на «Отменена»."""
        LoginPage(page, base_url).login(QA_USERNAME, QA_PASSWORD)
        AppointmentFormPage(page, base_url).book(SERVICE_NAME, future_date, free_slot)

        dashboard = DashboardPage(page, base_url)
        dashboard.open("/users/dashboard/")
        dashboard.cancel_appointment(SERVICE_NAME)

        assert dashboard.row_status(SERVICE_NAME) == "Отменена"

    def test_dashboard_empty_state_for_new_user(self, page, base_url, unique_suffix):
        """У свежезарегистрированного пользователя кабинет без записей."""
        RegisterPage(page, base_url).register(
            username=f"e2e_empty_{unique_suffix}",
            first_name="Пустой",
            last_name="Кабинет",
            email=f"e2e_empty_{unique_suffix}@example.com",
            password="e2ePass_123",
        )

        dashboard = DashboardPage(page, base_url)
        dashboard.open("/users/dashboard/")

        assert "У вас пока нет записей" in dashboard.empty_state_text()

"""Page Object Model для E2E-тестов DiaMed."""

from .appointment_form_page import AppointmentFormPage
from .base_page import BasePage
from .dashboard_page import DashboardPage
from .login_page import LoginPage
from .register_page import RegisterPage

__all__ = (
    "AppointmentFormPage",
    "BasePage",
    "DashboardPage",
    "LoginPage",
    "RegisterPage",
)

"""Тесты для users приложения."""

from datetime import date, time, timedelta

from django.urls import reverse

import pytest

from apps.users.models import Appointment, DiagnosticResult, UserProfile


@pytest.mark.django_db
class TestUserProfileModel:
    """Тесты модели UserProfile."""

    def test_create_user_profile(self, user):
        """Тест создания профиля пользователя."""
        profile = UserProfile.objects.create(
            user=user, phone="+7 (999) 123-45-67", date_of_birth=date(1990, 1, 1), address="г. Москва, ул. Тестовая, д. 1"
        )
        assert profile.user == user
        assert profile.phone == "+7 (999) 123-45-67"
        assert profile.date_of_birth == date(1990, 1, 1)

    def test_user_profile_str(self, user):
        """Тест строкового представления."""
        user.first_name = "Иван"
        user.last_name = "Иванов"
        user.save()
        profile = UserProfile.objects.create(user=user)
        str_repr = str(profile)
        assert "Профиль:" in str_repr
        assert "Иванов Иван" in str_repr or "Иван" in str_repr

    def test_user_profile_one_to_one(self, user):
        """Тест одного профиля на пользователя."""
        UserProfile.objects.create(user=user)
        # Попытка создать второй профиль для того же пользователя
        with pytest.raises(Exception):  # IntegrityError
            UserProfile.objects.create(user=user)


@pytest.mark.django_db
class TestAppointmentModel:
    """Тесты модели Appointment."""

    def test_create_appointment(self, user, sample_service):
        """Тест создания записи на приём."""
        appointment = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() + timedelta(days=1), time=time(10, 0), status="pending"
        )
        assert appointment.user == user
        assert appointment.service == sample_service
        assert appointment.status == "pending"

    def test_appointment_str(self, user, sample_service):
        """Тест строкового представления."""
        user.first_name = "Петр"
        user.last_name = "Петров"
        user.save()
        appointment = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() + timedelta(days=1), time=time(10, 0)
        )
        str_repr = str(appointment)
        assert "Петров" in str_repr or "Петр" in str_repr
        assert "Анализ крови" in str_repr

    def test_appointment_status_choices(self, user, sample_service):
        """Тест статусов записи."""
        statuses = ["pending", "confirmed", "completed", "cancelled"]
        for status in statuses:
            appointment = Appointment.objects.create(
                user=user, service=sample_service, date=date.today() + timedelta(days=1), time=time(10, 0), status=status
            )
            assert appointment.status == status

    def test_appointment_ordering(self, user, sample_service):
        """Тест сортировки записей."""
        today = date.today()
        Appointment.objects.create(user=user, service=sample_service, date=today + timedelta(days=2), time=time(10, 0))
        Appointment.objects.create(user=user, service=sample_service, date=today + timedelta(days=1), time=time(12, 0))
        appointments = list(Appointment.objects.all())
        # Первой должна быть более поздняя запись
        assert appointments[0].date == today + timedelta(days=2)

    def test_appointment_default_status(self, user, sample_service):
        """Тест статуса по умолчанию."""
        appointment = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() + timedelta(days=1), time=time(10, 0)
        )
        assert appointment.status == "pending"


@pytest.mark.django_db
class TestDiagnosticResultModel:
    """Тесты модели DiagnosticResult."""

    def test_create_diagnostic_result(self, user, sample_service):
        """Тест создания результата диагностики."""
        appointment = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() - timedelta(days=1), time=time(10, 0), status="completed"
        )
        result = DiagnosticResult.objects.create(
            appointment=appointment, conclusion="Показатели в норме", recommendations="Пройти через год", doctor="Иванов И.И."
        )
        assert result.appointment == appointment
        assert result.conclusion == "Показатели в норме"
        assert result.doctor == "Иванов И.И."
        assert result.is_normal is True

    def test_diagnostic_result_str(self, user, sample_service):
        """Тест строкового представления."""
        appointment = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() - timedelta(days=1), time=time(10, 0)
        )
        result = DiagnosticResult.objects.create(appointment=appointment, conclusion="Заключение", doctor="Врач")
        str_repr = str(result)
        assert "Результат:" in str_repr

    def test_diagnostic_result_one_to_one(self, user, sample_service):
        """Тест одного результата на запись."""
        appointment = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() - timedelta(days=1), time=time(10, 0)
        )
        DiagnosticResult.objects.create(appointment=appointment, conclusion="Заключение", doctor="Врач")
        # Попытка создать второй результат
        with pytest.raises(Exception):
            DiagnosticResult.objects.create(appointment=appointment, conclusion="Заключение 2", doctor="Врач 2")

    def test_diagnostic_result_ordering(self, user, sample_service):
        """Тест сортировки результатов."""
        appointment1 = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() - timedelta(days=2), time=time(10, 0)
        )
        appointment2 = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() - timedelta(days=1), time=time(10, 0)
        )
        DiagnosticResult.objects.create(appointment=appointment1, conclusion="Заключение 1", doctor="Врач")
        DiagnosticResult.objects.create(appointment=appointment2, conclusion="Заключение 2", doctor="Врач")
        results = list(DiagnosticResult.objects.all())
        # Первым должен быть более поздний результат
        assert results[0].result_date >= results[1].result_date


@pytest.mark.django_db
class TestUsersViewsAuth:
    """Тесты views авторизации."""

    def test_register_view_get(self, client):
        """Тест GET запроса на регистрацию."""
        response = client.get(reverse("users:register"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_register_view_post_valid(self, client):
        """Тест POST запроса с валидными данными."""
        data = {
            "username": "newuser",
            "first_name": "Новый",
            "last_name": "Пользователь",
            "email": "newuser@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        response = client.post(reverse("users:register"), data)
        assert response.status_code == 302  # Redirect after success

    def test_register_view_post_invalid(self, client):
        """Тест POST запроса с невалидными данными."""
        data = {
            "username": "newuser",
            "first_name": "Новый",
            "last_name": "Пользователь",
            "email": "invalid-email",
            "password1": "123",
            "password2": "456",
        }
        response = client.post(reverse("users:register"), data)
        assert response.status_code == 200  # Stay on page with errors

    def test_login_view_get(self, client):
        """Тест GET запроса на вход."""
        response = client.get(reverse("users:login"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_login_view_post_valid(self, client, user):
        """Тест POST запроса с валидными данными."""
        data = {"username": "testuser", "password": "testpass123"}
        response = client.post(reverse("users:login"), data)
        assert response.status_code == 302  # Redirect after success

    def test_login_view_post_invalid(self, client, user):
        """Тест POST запроса с невалидными данными."""
        data = {"username": "testuser", "password": "wrongpassword"}
        response = client.post(reverse("users:login"), data)
        assert response.status_code == 200  # Stay on page with errors

    def test_logout_view(self, authenticated_client):
        """Тест выхода."""
        response = authenticated_client.post(reverse("users:logout"))
        assert response.status_code == 302  # Redirect


@pytest.mark.django_db
class TestUsersViewsDashboard:
    """Тесты views личного кабинета."""

    def test_dashboard_view_authenticated(self, authenticated_client, user):
        """Тест личного кабинета для аутентифицированного пользователя."""
        response = authenticated_client.get(reverse("users:dashboard"))
        assert response.status_code == 200
        assert "appointments" in response.context
        assert "profile" in response.context

    def test_dashboard_view_redirect_not_authenticated(self, client):
        """Тест редиректа для неаутентифицированного пользователя."""
        response = client.get(reverse("users:dashboard"))
        assert response.status_code == 302  # Redirect to login

    def test_dashboard_shows_only_user_appointments(self, authenticated_client, user, sample_service):
        """Тест что пользователь видит только свои записи."""
        # Создаем запись для текущего пользователя
        Appointment.objects.create(user=user, service=sample_service, date=date.today() + timedelta(days=1), time=time(10, 0))
        # Создаем запись для другого пользователя
        other_user_data = {
            "username": "otheruser",
            "first_name": "Другой",
            "last_name": "Пользователь",
            "email": "other@example.com",
            "password": "otherpass123",
        }
        from django.contrib.auth.models import User

        other_user = User.objects.create_user(**other_user_data)
        Appointment.objects.create(
            user=other_user, service=sample_service, date=date.today() + timedelta(days=2), time=time(11, 0)
        )

        response = authenticated_client.get(reverse("users:dashboard"))
        assert response.status_code == 200
        # Должна быть только одна запись (для текущего пользователя)
        assert len(response.context["appointments"]) == 1


@pytest.mark.django_db
class TestUsersViewsProfile:
    """Тесты views профиля."""

    def test_profile_edit_view_authenticated(self, authenticated_client, user):
        """Тест редактирования профиля."""
        response = authenticated_client.get(reverse("users:profile_edit"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_profile_edit_view_post_valid(self, authenticated_client, user):
        """Тест сохранения профиля."""
        data = {"phone": "+7 (999) 999-99-99", "date_of_birth": "1990-01-01", "address": "Новый адрес"}
        response = authenticated_client.post(reverse("users:profile_edit"), data)
        assert response.status_code == 302  # Redirect after success
        # Проверка обновления
        profile = UserProfile.objects.get(user=user)
        assert profile.phone == "+7 (999) 999-99-99"


@pytest.mark.django_db
class TestUsersViewsAppointments:
    """Тесты views записей на приём."""

    def test_appointment_create_view_get(self, authenticated_client):
        """Тест GET запроса на создание записи."""
        response = authenticated_client.get(reverse("users:appointment_create"))
        assert response.status_code == 200
        assert "form" in response.context

    def test_appointment_create_view_post_valid(self, authenticated_client, sample_service):
        """Тест POST запроса с валидными данными."""
        tomorrow = date.today() + timedelta(days=1)
        data = {"service": sample_service.id, "date": tomorrow.isoformat(), "time": "10:00", "notes": "Тестовая запись"}
        response = authenticated_client.post(reverse("users:appointment_create"), data)
        assert response.status_code == 302  # Redirect after success
        assert Appointment.objects.count() == 1

    def test_appointment_create_view_post_past_date(self, authenticated_client, sample_service):
        """Тест что нельзя записаться на прошедшую дату."""
        yesterday = date.today() - timedelta(days=1)
        data = {"service": sample_service.id, "date": yesterday.isoformat(), "time": "10:00", "notes": "Тестовая запись"}
        response = authenticated_client.post(reverse("users:appointment_create"), data)
        assert response.status_code == 200  # Stay on page with errors

    def test_appointment_detail_view(self, authenticated_client, user, sample_service):
        """Тест детальной страницы записи."""
        appointment = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() + timedelta(days=1), time=time(10, 0)
        )
        response = authenticated_client.get(reverse("users:appointment_detail", kwargs={"pk": appointment.id}))
        assert response.status_code == 200
        assert "appointment" in response.context

    def test_appointment_detail_view_not_owner(self, authenticated_client, sample_service):
        """Тест что пользователь не видит чужие записи."""
        other_user_data = {
            "username": "otheruser",
            "first_name": "Другой",
            "last_name": "Пользователь",
            "email": "other@example.com",
            "password": "otherpass123",
        }
        from django.contrib.auth.models import User

        other_user = User.objects.create_user(**other_user_data)
        appointment = Appointment.objects.create(
            user=other_user, service=sample_service, date=date.today() + timedelta(days=1), time=time(10, 0)
        )
        response = authenticated_client.get(reverse("users:appointment_detail", kwargs={"pk": appointment.id}))
        assert response.status_code == 404  # Not found

    def test_appointment_cancel_view(self, authenticated_client, user, sample_service):
        """Тест отмены записи."""
        appointment = Appointment.objects.create(
            user=user, service=sample_service, date=date.today() + timedelta(days=1), time=time(10, 0), status="pending"
        )
        response = authenticated_client.post(reverse("users:appointment_cancel", kwargs={"pk": appointment.id}))
        assert response.status_code == 302  # Redirect after success
        # Проверка изменения статуса
        appointment.refresh_from_db()
        assert appointment.status == "cancelled"


@pytest.mark.django_db
class TestUsersForms:
    """Тесты forms users приложения."""

    def test_user_register_form_valid(self):
        """Тест валидной формы регистрации."""
        from apps.users.forms import UserRegisterForm

        data = {
            "username": "testuser",
            "first_name": "Тест",
            "last_name": "Тестов",
            "email": "test@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        form = UserRegisterForm(data)
        assert form.is_valid()

    def test_user_register_form_invalid_email(self):
        """Тест формы с невалидным email."""
        from apps.users.forms import UserRegisterForm

        data = {
            "username": "testuser",
            "first_name": "Тест",
            "last_name": "Тестов",
            "email": "not-an-email",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        form = UserRegisterForm(data)
        assert not form.is_valid()

    def test_appointment_form_valid(self, sample_service):
        """Тест валидной формы записи."""
        from apps.users.forms import AppointmentForm

        tomorrow = date.today() + timedelta(days=1)
        data = {"service": sample_service.id, "date": tomorrow.isoformat(), "time": "10:00", "notes": "Тест"}
        form = AppointmentForm(data)
        assert form.is_valid()

    def test_appointment_form_past_date_validation(self, sample_service):
        """Тест валидации даты в прошлом."""
        from apps.users.forms import AppointmentForm

        yesterday = date.today() - timedelta(days=1)
        data = {"service": sample_service.id, "date": yesterday.isoformat(), "time": "10:00", "notes": "Тест"}
        form = AppointmentForm(data)
        assert not form.is_valid()


@pytest.mark.django_db
class TestUsersUrls:
    """Тесты URL routing users приложения."""

    def test_register_url_resolves(self):
        """Тест разрешения URL регистрации."""
        url = reverse("users:register")
        assert url == "/users/register/"

    def test_login_url_resolves(self):
        """Тест разрешения URL входа."""
        url = reverse("users:login")
        assert url == "/users/login/"

    def test_dashboard_url_resolves(self):
        """Тест разрешения URL личного кабинета."""
        url = reverse("users:dashboard")
        assert url == "/users/dashboard/"

    def test_profile_edit_url_resolves(self):
        """Тест разрешения URL редактирования профиля."""
        url = reverse("users:profile_edit")
        assert url == "/users/profile/edit/"

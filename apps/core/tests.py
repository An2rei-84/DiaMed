"""Тесты для core приложения."""

from django.urls import reverse

import pytest

from apps.core.models import ContactForm


@pytest.mark.django_db
class TestContactFormModel:
    """Тесты модели ContactForm."""

    def test_create_contact_form(self):
        """Тест создания сообщения из формы связи."""
        contact = ContactForm.objects.create(name="Иван Иванов", email="ivan@example.com", message="Тестовое сообщение")
        assert contact.name == "Иван Иванов"
        assert contact.email == "ivan@example.com"
        assert contact.message == "Тестовое сообщение"
        assert contact.is_processed is False

    def test_contact_form_str(self):
        """Тест строкового представления ContactForm."""
        contact = ContactForm.objects.create(name="Петр Петров", email="petr@example.com", message="Сообщение")
        str_repr = str(contact)
        assert "Петр Петров" in str_repr
        assert contact.created_at.strftime("%d.%m.%Y") in str_repr

    def test_contact_form_ordering(self):
        """Тест сортировки ContactForm."""
        ContactForm.objects.create(name="Первый", email="first@example.com", message="Сообщение 1")
        ContactForm.objects.create(name="Второй", email="second@example.com", message="Сообщение 2")
        contacts = list(ContactForm.objects.all())
        # Первым должен быть более поздний
        assert contacts[0].name == "Второй"
        assert contacts[1].name == "Первый"


@pytest.mark.django_db
class TestCoreViews:
    """Тесты views core приложения."""

    def test_index_view(self, client, sample_service, sample_contact):
        """Тест главной страницы."""
        response = client.get(reverse("core:index"))
        assert response.status_code == 200
        assert "services" in response.context
        assert "contacts" in response.context

    def test_index_view_without_contacts(self, client, sample_service):
        """Тест главной страницы без контактов."""
        response = client.get(reverse("core:index"))
        assert response.status_code == 200
        assert response.context["contacts"] is None

    def test_contact_form_submit_get(self, client):
        """Тест GET запроса на форму связи."""
        response = client.get(reverse("core:contact"))
        assert response.status_code == 302  # Redirect

    def test_contact_form_submit_post_valid(self, client):
        """Тест POST запроса с валидными данными."""
        data = {"name": "Тестовый пользователь", "email": "test@example.com", "message": "Тестовое сообщение"}
        response = client.post(reverse("core:contact"), data)
        assert response.status_code == 302  # Redirect after success
        assert ContactForm.objects.count() == 1

    def test_contact_form_submit_post_invalid(self, client):
        """Тест POST запроса с невалидными данными."""
        data = {
            "name": "",  # Пустое имя
            "email": "invalid-email",  # Невалидный email
            "message": "x" * 10,  # Короткое сообщение
        }
        response = client.post(reverse("core:contact"), data)
        # Должен остаться на странице или перенаправиться
        assert response.status_code == 302


@pytest.mark.django_db
class TestCoreForms:
    """Тесты форм core приложения."""

    def test_contact_form_valid(self):
        """Тест валидной формы связи."""
        from apps.core.forms import ContactForm as ContactFormForm

        data = {"name": "Иван", "email": "ivan@example.com", "message": "Тестовое сообщение"}
        form = ContactFormForm(data)
        assert form.is_valid()

    def test_contact_form_invalid_empty_fields(self):
        """Тест формы связи с пустыми полями."""
        from apps.core.forms import ContactForm as ContactFormForm

        data = {"name": "", "email": "", "message": ""}
        form = ContactFormForm(data)
        assert not form.is_valid()

    def test_contact_form_invalid_email(self):
        """Тест формы связи с невалидным email."""
        from apps.core.forms import ContactForm as ContactFormForm

        data = {"name": "Иван", "email": "not-an-email", "message": "Сообщение"}
        form = ContactFormForm(data)
        assert not form.is_valid()


@pytest.mark.django_db
class TestCoreUrls:
    """Тесты URL routing core приложения."""

    def test_index_url_resolves(self):
        """Тест разрешения URL главной страницы."""
        url = reverse("core:index")
        assert url == "/"

    def test_contact_url_resolves(self):
        """Тест разрешения URL формы связи."""
        url = reverse("core:contact")
        assert url == "/contact/"

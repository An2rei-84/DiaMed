"""Тесты для contacts приложения."""

from django.urls import reverse

import pytest

from apps.contacts.models import Contact


@pytest.mark.django_db
class TestContactModel:
    """Тесты модели Contact."""

    def test_create_contact(self):
        """Тест создания контактной информации."""
        contact = Contact.objects.create(
            address="г. Москва, ул. Примерная, д. 1",
            phone="+7 (495) 123-45-67",
            email="info@diamed.ru",
            working_hours="Пн-Пт: 8:00-20:00",
        )
        assert contact.address == "г. Москва, ул. Примерная, д. 1"
        assert contact.phone == "+7 (495) 123-45-67"
        assert contact.email == "info@diamed.ru"

    def test_contact_str(self):
        """Тест строкового представления."""
        contact = Contact.objects.create(
            address="г. Санкт-Петербург", phone="+7 (812) 111-22-33", email="spb@diamed.ru", working_hours="Пн-Пт: 9:00-18:00"
        )
        str_repr = str(contact)
        assert "г. Санкт-Петербург" in str_repr
        assert "+7 (812) 111-22-33" in str_repr

    def test_contact_with_map_url(self):
        """Тест контакта с URL карты."""
        contact = Contact.objects.create(
            address="Адрес", phone="Телефон", email="test@test.ru", working_hours="Время", map_url="https://maps.google.com"
        )
        assert contact.map_url == "https://maps.google.com"

    def test_contact_with_map_embed(self):
        """Тест контакта с кодом внедрения карты."""
        map_code = '<iframe src="..."></iframe>'
        contact = Contact.objects.create(
            address="Адрес", phone="Телефон", email="test@test.ru", working_hours="Время", map_embed=map_code
        )
        assert contact.map_embed == map_code

    def test_contact_single_instance(self, db):
        """Тест что может быть только один экземпляр Contact."""
        Contact.objects.create(
            address="Первый адрес", phone="+7 (495) 111-11-11", email="first@diamed.ru", working_hours="Пн-Пт: 9:00-18:00"
        )

        # Попытка создать второй экземпляр
        with pytest.raises(ValueError, match="Может быть только один экземпляр Contact"):
            Contact.objects.create(
                address="Второй адрес", phone="+7 (495) 222-22-22", email="second@diamed.ru", working_hours="Пн-Пт: 9:00-18:00"
            )

    def test_contact_update_existing(self, db):
        """Тест обновления существующего контакта."""
        contact = Contact.objects.create(
            address="Старый адрес", phone="+7 (495) 111-11-11", email="old@diamed.ru", working_hours="Пн-Пт: 9:00-18:00"
        )
        # Обновление разрешено
        contact.address = "Новый адрес"
        contact.save()
        updated_contact = Contact.objects.first()
        assert updated_contact.address == "Новый адрес"


@pytest.mark.django_db
class TestContactsViews:
    """Тесты views contacts приложения."""

    def test_contacts_view_with_data(self, client, sample_contact):
        """Тест страницы контактов с данными."""
        response = client.get(reverse("contacts:index"))
        assert response.status_code == 200
        assert "contacts" in response.context
        assert response.context["contacts"] is not None
        assert response.context["contacts"].address == "г. Москва, ул. Примерная, д. 1"

    def test_contacts_view_without_data(self, client):
        """Тест страницы контактов без данных."""
        response = client.get(reverse("contacts:index"))
        assert response.status_code == 200
        assert "contacts" in response.context
        assert response.context["contacts"] is None

    def test_contacts_view_template_used(self, client, sample_contact):
        """Тест используемого шаблона."""
        response = client.get(reverse("contacts:index"))
        assert response.status_code == 200
        # Проверка шаблона
        assert "contacts/index.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestContactsUrls:
    """Тесты URL routing contacts приложения."""

    def test_contacts_url_resolves(self):
        """Тест разрешения URL страницы контактов."""
        url = reverse("contacts:index")
        assert url == "/contacts/"

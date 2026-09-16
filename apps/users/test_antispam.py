"""Тесты анти-спама веб-форм: rate limiting регистраций и входа, honeypot."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client

import pytest

from apps.users.views import LOGIN_RATE_LIMITED_MESSAGE, REGISTER_RATE_LIMITED_MESSAGE

REGISTER_URL = "/users/register/"
LOGIN_URL = "/users/login/"


@pytest.fixture(autouse=True)
def _clear_cache():
    """Счётчики лимитов живут в кэше — чистим между тестами."""
    cache.clear()
    yield


def _register_payload(number):
    """Валидные данные регистрации; honeypot не заполняется — как у человека."""
    return {
        "username": f"spam_{number}",
        "first_name": "Тест",
        "last_name": "Тестов",
        "email": f"spam_{number}@example.com",
        "password1": "Testpass123!",
        "password2": "Testpass123!",
    }


@pytest.mark.django_db
class TestRegisterRateLimit:
    """Ограничение регистраций с одного IP."""

    def test_blocks_registrations_over_limit(self, client, settings):
        """Регистрации до лимита создают пользователей, следующая — отклоняется."""
        settings.RATE_LIMIT_REGISTER = (2, 3600)

        for number in range(2):
            response = client.post(REGISTER_URL, _register_payload(number))
            assert response.status_code == 302
        assert User.objects.count() == 2

        response = client.post(REGISTER_URL, _register_payload(3))

        assert response.status_code == 200
        assert REGISTER_RATE_LIMITED_MESSAGE in response.content.decode()
        assert User.objects.count() == 2

    def test_limit_counter_is_per_ip(self, settings):
        """Лимит копится по IP: другой адрес не наследует чужой счётчик."""
        settings.RATE_LIMIT_REGISTER = (1, 3600)

        first_ip = Client(REMOTE_ADDR="203.0.113.1")
        other_ip = Client(REMOTE_ADDR="203.0.113.7")

        assert first_ip.post(REGISTER_URL, _register_payload(1)).status_code == 302
        assert other_ip.post(REGISTER_URL, _register_payload(2)).status_code == 302


@pytest.mark.django_db
class TestRegisterHoneypot:
    """Скрытое поле-ловушка для ботов."""

    def test_filled_honeypot_fakes_success_without_user(self, client):
        """Заполненный honeypot отдаёт «успех», но пользователя не создаёт."""
        payload = _register_payload("bot") | {"website": "http://spam.example"}

        response = client.post(REGISTER_URL, payload)

        assert response.status_code == 302
        assert not User.objects.filter(username="spam_bot").exists()

    def test_real_user_without_honeypot_registers(self, client):
        """Обычная регистрация (honeypot пуст) работает как раньше."""
        response = client.post(REGISTER_URL, _register_payload(1))

        assert response.status_code == 302
        assert User.objects.filter(username="spam_1").exists()


@pytest.mark.django_db
class TestLoginRateLimit:
    """Ограничение попыток входа с одного IP."""

    def test_blocks_login_attempts_over_limit(self, client, settings, user, user_data):
        """После лимита не пускает даже с верным паролем, до истечения окна."""
        settings.RATE_LIMIT_LOGIN = (2, 900)

        for _ in range(2):
            client.post(LOGIN_URL, {"username": "testuser", "password": "wrong"})

        response = client.post(LOGIN_URL, {"username": "testuser", "password": user_data["password"]})

        assert response.status_code == 200
        assert LOGIN_RATE_LIMITED_MESSAGE in response.content.decode()
        assert "_auth_user_id" not in client.session

    def test_successful_logins_within_limit_work(self, client, settings, user, user_data):
        """Попытки внутри лимита (в том числе успешные) работают штатно."""
        settings.RATE_LIMIT_LOGIN = (3, 900)

        response = client.post(LOGIN_URL, {"username": "testuser", "password": user_data["password"]})

        assert response.status_code == 302
        assert response.url == "/users/dashboard/"

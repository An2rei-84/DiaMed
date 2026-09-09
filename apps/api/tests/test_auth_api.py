"""Тесты JWT-аутентификации API."""

from django.contrib.auth.models import User

import pytest

TOKEN_URL = "/api/auth/token/"
REFRESH_URL = "/api/auth/token/refresh/"


@pytest.mark.django_db
class TestJWTAuth:
    """Получение и обновление JWT-токенов."""

    def test_obtain_token_success(self, api_client, user):
        """Валидные учётные данные дают access и refresh токены."""
        response = api_client.post(TOKEN_URL, {"username": "testuser", "password": "testpass123"})

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_obtain_token_wrong_password(self, api_client, user):
        """Неверный пароль — 401."""
        response = api_client.post(TOKEN_URL, {"username": "testuser", "password": "wrong"})

        assert response.status_code == 401

    def test_refresh_token(self, api_client, user):
        """Refresh-токен выдаёт новый access-токен."""
        refresh = api_client.post(TOKEN_URL, {"username": "testuser", "password": "testpass123"}).data["refresh"]

        response = api_client.post(REFRESH_URL, {"refresh": refresh})

        assert response.status_code == 200
        assert "access" in response.data

    def test_bearer_token_grants_access(self, api_client, user):
        """С Bearer-токеном эндпоинт записей отвечает 200."""
        token = api_client.post(TOKEN_URL, {"username": "testuser", "password": "testpass123"}).data["access"]

        response = api_client.get("/api/appointments/", HTTP_AUTHORIZATION=f"Bearer {token}")

        assert response.status_code == 200

    def test_without_token_unauthorized(self, api_client):
        """Без токена эндпоинт записей отвечает 401."""
        response = api_client.get("/api/appointments/")

        assert response.status_code == 401

    def test_session_auth_still_works(self, client, user):
        """Сессии веб-интерфейса продолжают работать с API."""
        client.force_login(User.objects.get(username="testuser"))

        response = client.get("/api/appointments/")

        assert response.status_code == 200

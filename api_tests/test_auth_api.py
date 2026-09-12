"""Black-box тесты JWT-аутентификации (/api/auth/token/)."""

import requests

QA_USERNAME = "qa_api"
QA_PASSWORD = "qa_pass_123"


class TestTokenAuth:
    """Получение и обновление JWT-токенов."""

    def test_obtain_token_success(self, base_url):
        """Валидные креды возвращают access и refresh."""
        response = requests.post(
            f"{base_url}/api/auth/token/",
            json={"username": QA_USERNAME, "password": QA_PASSWORD},
            timeout=10,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["access"]
        assert body["refresh"]

    def test_obtain_token_wrong_password(self, base_url):
        """Неверный пароль — 401."""
        response = requests.post(
            f"{base_url}/api/auth/token/",
            json={"username": QA_USERNAME, "password": "wrong"},
            timeout=10,
        )

        assert response.status_code == 401

    def test_refresh_token(self, base_url):
        """Refresh-токен выдаёт новый access."""
        refresh = requests.post(
            f"{base_url}/api/auth/token/",
            json={"username": QA_USERNAME, "password": QA_PASSWORD},
            timeout=10,
        ).json()["refresh"]

        response = requests.post(f"{base_url}/api/auth/token/refresh/", json={"refresh": refresh}, timeout=10)

        assert response.status_code == 200
        assert response.json()["access"]

    def test_appointments_require_auth(self, base_url):
        """Без токена список записей недоступен — 401."""
        response = requests.get(f"{base_url}/api/appointments/", timeout=10)

        assert response.status_code == 401

    def test_invalid_token_rejected(self, base_url):
        """Мусорный токен отклоняется — 401."""
        response = requests.get(
            f"{base_url}/api/appointments/",
            headers={"Authorization": "Bearer not-a-jwt"},
            timeout=10,
        )

        assert response.status_code == 401

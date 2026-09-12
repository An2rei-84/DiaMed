"""Фикстуры API black-box тестов: живой Django-сервер и авторизация по JWT.

Сервер поднимается один раз на сессию на SQLite с демо-данными (manage.py qa_seed).
Если задана переменная окружения API_BASE_URL, тесты идут на существующий сервер.
"""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_PORT = int(os.environ.get("API_TESTS_PORT", "8022"))
ARTIFACTS_DIR = Path(__file__).resolve().parent / "api-tests-artifacts"

QA_USERNAME = "qa_api"
QA_PASSWORD = "qa_pass_123"
QA2_USERNAME = "qa_api2"
QA2_PASSWORD = "qa_pass_456"


def _wait_for_server(url, timeout=60):
    """Ждёт, пока сервер начнёт отвечать 200 на корень."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"Сервер не ответил за {timeout} секунд: {url} (лог: {ARTIFACTS_DIR / 'server.log'})")


@pytest.fixture(scope="session")
def base_url():
    """URL API-приложения под тестом: свой сервер или внешнее окружение."""
    external = os.environ.get("API_BASE_URL")
    if external:
        yield external.rstrip("/")
        return

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["USE_SQLITE"] = "True"
    env["DEBUG"] = "True"
    env["CELERY_TASK_ALWAYS_EAGER"] = "True"

    def manage(*args):
        """Запускает команду manage.py в окружении тестового сервера."""
        subprocess.run([sys.executable, "manage.py", *args], cwd=PROJECT_ROOT, env=env, check=True)

    manage("migrate", "--noinput")
    manage("qa_seed")

    log = open(ARTIFACTS_DIR / "server.log", "w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{SERVER_PORT}", "--noreload"],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_server(f"http://127.0.0.1:{SERVER_PORT}/")
        yield f"http://127.0.0.1:{SERVER_PORT}"
    finally:
        process.terminate()
        process.wait(timeout=10)
        log.close()


@pytest.fixture
def access_token(base_url):
    """JWT access-токен основного демо-пользователя."""
    response = requests.post(
        f"{base_url}/api/auth/token/",
        json={"username": QA_USERNAME, "password": QA_PASSWORD},
        timeout=10,
    )
    assert response.status_code == 200, f"Не получили токен: {response.text}"
    return response.json()["access"]


@pytest.fixture
def auth_headers(access_token):
    """Заголовки с JWT основного пользователя."""
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_headers2(base_url):
    """Заголовки с JWT второго пользователя (для проверок изоляции данных)."""
    response = requests.post(
        f"{base_url}/api/auth/token/",
        json={"username": QA2_USERNAME, "password": QA2_PASSWORD},
        timeout=10,
    )
    assert response.status_code == 200, f"Не получили токен второго пользователя: {response.text}"
    return {"Authorization": f"Bearer {response.json()['access']}"}


@pytest.fixture
def tomorrow():
    """Дата приёма: завтра."""
    from datetime import date, timedelta

    return date.today() + timedelta(days=1)


@pytest.fixture
def service_pk(base_url):
    """PK демо-услуги по slug (через публичный каталог, как положено чёрному ящику)."""
    response = requests.get(f"{base_url}/api/services/", params={"search": "крови"}, timeout=10)
    for item in response.json()["results"]:
        if item["slug"] == "analiz-krovi":
            return item["id"]
    raise AssertionError("Услуга analiz-krovi не найдена в каталоге")


@pytest.fixture
def free_slots(base_url, service_pk, tomorrow):
    """Список свободных слотов демо-услуги на завтра.

    Слоты берутся из available-slots, а не константами: занятое прошлыми
    прогонами время не предлагается — тесты остаются идемпотентными.
    """
    response = requests.get(
        f"{base_url}/api/appointments/available-slots/",
        params={"service": "analiz-krovi", "date": str(tomorrow)},
        timeout=10,
    )
    slots = response.json()["available_slots"]
    assert len(slots) >= 8, f"Ожидали не менее 8 свободных слотов, получили {len(slots)}"
    return slots

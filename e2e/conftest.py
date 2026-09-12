"""Фикстуры E2E-тестов: автоматический подъём живого Django-сервера.

Сервер поднимается один раз на сессию на SQLite с демо-данными (manage.py qa_seed).
Если задана переменная окружения E2E_BASE_URL, тесты идут на существующий
сервер без подъёма своего — так можно прогнать смок на любое окружение.
"""

import os
import subprocess
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_PORT = int(os.environ.get("E2E_PORT", "8021"))
ARTIFACTS_DIR = Path(__file__).resolve().parent / "e2e-artifacts"


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
    """URL приложения под тестом: свой сервер или внешнее окружение."""
    external = os.environ.get("E2E_BASE_URL")
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
def future_date():
    """Дата приёма для тестов: через две недели (не пересекается с прошедшими проверками)."""
    return date.today() + timedelta(days=14)


@pytest.fixture
def unique_suffix():
    """Уникальный суффикс для логинов/email, чтобы повторные прогоны не конфликтовали."""
    return f"{int(time.time())}_{os.getpid()}"


@pytest.fixture
def free_slot(base_url, future_date):
    """Первый свободный слот для демо-услуги на будущую дату (через публичный API).

    Берём слот из available-slots, а не константу: слоты, забронированные
    прошлыми прогонами, не предлагаются — тесты остаются идемпотентными.
    """
    response = requests.get(
        f"{base_url}/api/appointments/available-slots/",
        params={"service": "analiz-krovi", "date": future_date.isoformat()},
        timeout=10,
    )
    slots = response.json().get("available_slots", [])
    assert slots, f"Нет свободных слотов на {future_date} — похоже, данные кто-то забронировал целиком"
    return slots[0]

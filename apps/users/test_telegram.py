"""Тесты Telegram-интеграции: отправка, привязка аккаунта, уведомления в задачах."""

from django.urls import reverse

import pytest
import requests as requests_lib

from apps.users.management.commands.telegram_bot import BAD_CODE_TEXT, HINT_TEXT, Command
from apps.users.models import UserProfile
from apps.users.tasks import send_appointment_confirmation, send_appointment_reminders
from apps.users.telegram import send_telegram_message

BOT_COMMAND_MODULE = "apps.users.management.commands.telegram_bot.send_telegram_message"


@pytest.fixture
def profile(user):
    """Профиль тестового пользователя."""
    return UserProfile.objects.create(user=user)


@pytest.fixture
def bound_profile(profile):
    """Профиль с привязанным Telegram."""
    profile.telegram_chat_id = 424242
    profile.save(update_fields=("telegram_chat_id",))
    return profile


class TestSendTelegramMessage:
    """Функция отправки сообщения через Bot API."""

    def test_no_token_disabled(self, monkeypatch):
        """Без токена отправка отключена: HTTP-запрос не выполняется."""
        monkeypatch.setattr("apps.users.telegram.settings.TELEGRAM_BOT_TOKEN", "")

        def fail_post(*args, **kwargs):
            raise AssertionError("HTTP-запрос не должен выполняться без токена")

        monkeypatch.setattr("apps.users.telegram.requests.post", fail_post)

        assert send_telegram_message(1, "привет") is False

    def test_send_success(self, monkeypatch):
        """Успешный ответ API — True, запрос отправлен с chat_id и текстом."""
        monkeypatch.setattr("apps.users.telegram.settings.TELEGRAM_BOT_TOKEN", "123:abc")
        calls = {}

        def fake_post(url, json=None, timeout=None):
            calls["url"] = url
            calls["json"] = json

            class Response:
                status_code = 200

            return Response()

        monkeypatch.setattr("apps.users.telegram.requests.post", fake_post)

        assert send_telegram_message(424242, "привет") is True
        assert "bot123:abc/sendMessage" in calls["url"]
        assert calls["json"] == {"chat_id": 424242, "text": "привет"}

    def test_send_api_error_returns_false(self, monkeypatch):
        """Не-200 ответ API — False."""
        monkeypatch.setattr("apps.users.telegram.settings.TELEGRAM_BOT_TOKEN", "123:abc")

        def fake_post(url, json=None, timeout=None):
            class Response:
                status_code = 400

            return Response()

        monkeypatch.setattr("apps.users.telegram.requests.post", fake_post)

        assert send_telegram_message(424242, "привет") is False

    def test_send_network_error_returns_false(self, monkeypatch):
        """Сетевая ошибка не роняет вызывающий код — False."""
        monkeypatch.setattr("apps.users.telegram.settings.TELEGRAM_BOT_TOKEN", "123:abc")

        def fake_post(url, json=None, timeout=None):
            raise requests_lib.ConnectionError("нет сети")

        monkeypatch.setattr("apps.users.telegram.requests.post", fake_post)

        assert send_telegram_message(424242, "привет") is False


class TestTelegramBotCommand:
    """Обработка обновлений бота: привязка аккаунта по коду."""

    @pytest.fixture
    def command(self):
        """Экземпляр команды telegram_bot для вызова handle_update напрямую."""
        return Command()

    def test_start_with_valid_code_binds_chat(self, command, profile, monkeypatch):
        """/start <код> сохраняет chat_id в профиле и подтверждает привязку."""
        code = profile.ensure_telegram_link_code()
        sent = []
        monkeypatch.setattr(BOT_COMMAND_MODULE, lambda chat_id, text: sent.append((chat_id, text)) or True)

        command.handle_update({"update_id": 1, "message": {"chat": {"id": 777}, "text": f"/start {code}"}})

        profile.refresh_from_db()
        assert profile.telegram_chat_id == 777
        assert sent and "привязан" in sent[0][1]

    def test_start_with_unknown_code_rejected(self, command, profile, monkeypatch):
        """Неверный код не привязывает чат и просит актуальный код."""
        sent = []
        monkeypatch.setattr(BOT_COMMAND_MODULE, lambda chat_id, text: sent.append(text) or True)

        command.handle_update({"update_id": 1, "message": {"chat": {"id": 777}, "text": "/start deadbeef"}})

        profile.refresh_from_db()
        assert profile.telegram_chat_id is None
        assert sent == [BAD_CODE_TEXT]

    def test_start_without_code_rejected(self, command, profile, monkeypatch):
        """/start без кода — подсказка про код, привязки нет."""
        sent = []
        monkeypatch.setattr(BOT_COMMAND_MODULE, lambda chat_id, text: sent.append(text) or True)

        command.handle_update({"update_id": 1, "message": {"chat": {"id": 777}, "text": "/start"}})

        profile.refresh_from_db()
        assert profile.telegram_chat_id is None
        assert sent == [BAD_CODE_TEXT]

    def test_other_command_gets_hint(self, command, monkeypatch):
        """Произвольный текст — подсказка."""
        sent = []
        monkeypatch.setattr(BOT_COMMAND_MODULE, lambda chat_id, text: sent.append(text) or True)

        command.handle_update({"update_id": 1, "message": {"chat": {"id": 777}, "text": "здравствуйте"}})

        assert sent == [HINT_TEXT]

    def test_update_without_message_ignored(self, command, monkeypatch):
        """Обновление без сообщения не вызывает отправку и не падает."""
        monkeypatch.setattr(
            BOT_COMMAND_MODULE,
            lambda chat_id, text: (_ for _ in ()).throw(AssertionError("не должно отправляться")),
        )

        command.handle_update({"update_id": 1})


class TestTaskNotifications:
    """Дублирование уведомлений в Telegram из Celery-задач."""

    def test_confirmation_sent_to_telegram(self, appointment, bound_profile, monkeypatch):
        """Создание записи у привязанного пользователя шлёт сообщение в чат."""
        sent = []
        monkeypatch.setattr("apps.users.tasks.send_telegram_message", lambda chat_id, text: sent.append(chat_id) or True)

        send_appointment_confirmation(appointment.pk)

        assert sent == [424242]

    def test_confirmation_skipped_without_telegram(self, appointment, profile, monkeypatch):
        """Непривязанный пользователь не получает Telegram-уведомление."""

        def fail_send(chat_id, text):
            raise AssertionError("не должно отправляться")

        monkeypatch.setattr("apps.users.tasks.send_telegram_message", fail_send)

        send_appointment_confirmation(appointment.pk)

    def test_reminder_sent_to_telegram(self, appointment, bound_profile, monkeypatch, tomorrow):
        """Напоминание о завтрашнем приёме дублируется в чат."""
        appointment.date = tomorrow
        appointment.save()
        sent = []
        monkeypatch.setattr("apps.users.tasks.send_telegram_message", lambda chat_id, text: sent.append(chat_id) or True)

        send_appointment_reminders()

        assert sent == [424242]


class TestDashboardTelegramLink:
    """Привязка Telegram в личном кабинете."""

    def test_dashboard_shows_link_code(self, authenticated_client, profile):
        """При заходе в кабинет генерируется код привязки и показывается инструкция."""
        response = authenticated_client.get(reverse("users:dashboard"))

        assert response.status_code == 200
        profile.refresh_from_db()
        assert profile.telegram_link_code
        assert response.context["telegram_code"] == profile.telegram_link_code
        assert response.context["telegram_bot_username"]


@pytest.mark.django_db
class TestRegistrationWithLinkCode:
    """Регрессия: уникальный код привязки не должен ломать массовую регистрацию."""

    def _register(self, username):
        """Регистрирует пользователя через веб-форму (отдельный клиент)."""
        from django.test import Client

        data = {
            "username": username,
            "first_name": "Иван",
            "last_name": "Тестов",
            "email": f"{username}@example.com",
            "password1": "e2ePass_123",
            "password2": "e2ePass_123",
        }
        return Client().post(reverse("users:register"), data)

    def test_two_registrations_in_a_row(self, db):
        """Вторая регистрация подряд не падает из-за UNIQUE кода привязки у профилей."""
        assert self._register("reg_first").status_code == 302
        assert self._register("reg_second").status_code == 302

        codes = list(UserProfile.objects.exclude(telegram_link_code__isnull=True).values_list("telegram_link_code", flat=True))
        assert len(codes) == len(set(codes)), "Коды привязки у профилей не уникальны"

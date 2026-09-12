"""Команда Telegram-бота: long polling и привязка аккаунтов по коду."""

import time

from django.conf import settings
from django.core.management.base import BaseCommand

import requests

from apps.users.models import UserProfile
from apps.users.telegram import send_telegram_message

TELEGRAM_API_URL = "https://api.telegram.org"

HINT_TEXT = "Отправьте /start <код> из личного кабинета, чтобы получать уведомления о приёмах."
BAD_CODE_TEXT = "Код не найден. Возьмите актуальный код в личном кабинете и отправьте /start <код>."


class Command(BaseCommand):
    """Запускает бесконечный long polling обновлений Telegram-бота."""

    help = "Telegram-бот: long polling; команда /start <код> привязывает Telegram к аккаунту сайта"

    def add_arguments(self, parser):
        """Таймаут long polling в секундах."""
        parser.add_argument("--poll-timeout", type=int, default=25)

    def handle(self, *args, **options):
        """Цикл опроса getUpdates; не падает при сетевых сбоях."""
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.stderr.write("TELEGRAM_BOT_TOKEN не задан — укажите токен бота в окружении.")
            return
        self.stdout.write(self.style.SUCCESS("Telegram-бот запущен (long polling)"))
        offset = 0
        poll_timeout = options["poll_timeout"]
        while True:
            try:
                response = requests.get(
                    f"{TELEGRAM_API_URL}/bot{token}/getUpdates",
                    params={"offset": offset + 1, "timeout": poll_timeout},
                    timeout=poll_timeout + 10,
                )
                for update in response.json().get("result", []):
                    offset = max(offset, update["update_id"])
                    self.handle_update(update)
            except (requests.RequestException, ValueError):
                self.stderr.write("Ошибка обращения к Telegram API, повтор через 5 секунд")
                time.sleep(5)

    def handle_update(self, update):
        """Обрабатывает одно обновление: /start <код> привязывает аккаунт к чату."""
        message = update.get("message") or {}
        chat_id = (message.get("chat") or {}).get("id")
        text = (message.get("text") or "").strip()
        if not chat_id:
            return

        parts = text.split(maxsplit=1)
        if parts[0] != "/start":
            send_telegram_message(chat_id, HINT_TEXT)
            return

        code = parts[1].strip() if len(parts) > 1 else ""
        profile = None
        if code:
            profile = UserProfile.objects.filter(telegram_link_code=code).select_related("user").first()
        if profile is None:
            send_telegram_message(chat_id, BAD_CODE_TEXT)
            return

        profile.telegram_chat_id = chat_id
        profile.save(update_fields=("telegram_chat_id",))
        user = profile.user
        send_telegram_message(
            chat_id,
            f"✅ Аккаунт {user.get_full_name() or user.username} привязан! " "Буду присылать напоминания о приёмах.",
        )
        self.stdout.write(f"Привязан chat {chat_id} к профилю {user.username}")

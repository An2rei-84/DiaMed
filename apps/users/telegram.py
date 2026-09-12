"""Интеграция с Telegram Bot API: отправка сообщений пользователям."""

import logging

from django.conf import settings

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org"
SEND_TIMEOUT = 10


def send_telegram_message(chat_id, text):
    """Отправляет сообщение в Telegram; возвращает True при успехе.

    Без настроенного токена (TELEGRAM_BOT_TOKEN) отправка отключена —
    функция сразу возвращает False, чтобы задачи не падали в dev-режиме.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False
    try:
        response = requests.post(
            f"{TELEGRAM_API_URL}/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=SEND_TIMEOUT,
        )
    except requests.RequestException:
        logger.warning("Telegram API недоступен при отправке в chat %s", chat_id, exc_info=True)
        return False
    if response.status_code != 200:
        logger.warning("Telegram sendMessage вернул %s для chat %s", response.status_code, chat_id)
        return False
    return True

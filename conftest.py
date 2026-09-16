"""Общие хуки pytest: применяются до инициализации Django.

Лимиты анти-спама в тестах задраны: кэш общий на весь прогон, а сквозные
тесты (unit, api black-box, e2e) постят регистрации/логины много раз.
Тесты самих лимитов понижают их точечно через settings-фикстуру и чистят кэш.
"""

import os

os.environ.setdefault("RATE_LIMIT_REGISTER", "1000/hour")
os.environ.setdefault("RATE_LIMIT_LOGIN", "1000/hour")
os.environ.setdefault("API_AUTH_TOKEN_THROTTLE_RATE", "1000/min")

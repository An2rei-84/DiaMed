"""Анти-спам: rate limiting на кэше Django, без внешних зависимостей.

В проде кэш — Redis (общий для всех воркеров Gunicorn), в тестах — LocMem.
Окно фиксированное: на его границе возможен короткий всплеск вдвое больше
лимита, для отсечения спам-ботов этого достаточно.
"""

from django.core.cache import cache


def is_rate_limited(key, limit, window_seconds):
    """Учитывает событие `key` и возвращает True, если лимит исчерпан.

    Счётчик хранится в кэше с TTL = окно: первый запрос создаёт ключ
    (cache.add атомарен), последующие инкрементируют, не продлевая TTL.
    """
    try:
        hits = cache.incr(key)
    except ValueError:
        # Ключа ещё нет — заводим с единицы и TTL окна
        cache.add(key, 1, timeout=window_seconds)
        hits = 1
    return hits > limit

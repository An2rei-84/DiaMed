# DiaMed — сайт медицинского диагностического центра

[![CI/CD Pipeline](https://github.com/An2rei-84/DiaMed/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/An2rei-84/DiaMed/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-4.2_LTS-green)
![Tests](https://img.shields.io/badge/tests-147_passed-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)

Полнофункциональный веб-сайт медицинского диагностического центра: каталог услуг, запись на приём
с проверкой свободных слотов, личный кабинет пациента с результатами диагностики, REST API
с JWT-аутентификацией и асинхронные email-уведомления на Celery.

## Возможности

- 🏥 **Каталог услуг** — категории, цены, длительность, подготовка к процедурам
- 📅 **Запись на приём** — через сайт и REST API, с проверкой занятости слотов (8:00–20:00, шаг 30 мин)
- 👤 **Личный кабинет** — записи, статусы, результаты диагностики
- 🔌 **REST API** — DRF + JWT, фильтры, поиск, пагинация, rate limiting
- 📚 **Документация API** — Swagger UI и ReDoc по OpenAPI-схеме (drf-spectacular)
- ✉️ **Уведомления** — письмо-подтверждение при записи и напоминания за день (Celery + Celery Beat)
- ⚡ **Кэширование** — Redis для списка услуг
- 🔐 **Админ-панель** — управление услугами, записями, результатами и контентом
- ✅ **139 тестов, покрытие 99%**, CI/CD с автодеплоем Docker-образа

## Стек

| Слой | Технологии |
|------|-----------|
| Backend | Python 3.11, Django 4.2 LTS, Django REST Framework, SimpleJWT, django-filter |
| API-документация | drf-spectacular (OpenAPI 3, Swagger UI, ReDoc) |
| Асинхронность | Celery 5, Celery Beat, Redis 7 (брокер и кэш) |
| База данных | PostgreSQL 15 (SQLite для локальной разработки) |
| Инфраструктура | Docker, Docker Compose, Gunicorn, WhiteNoise |
| Качество | pytest, pytest-cov, factory-boy, flake8, black, isort, pre-commit |
| CI/CD | GitHub Actions (линтинг → тесты → сборка → деплой) |

## Архитектура

```mermaid
flowchart LR
    B[Браузер] --> G[Gunicorn]
    G --> D[Django]
    D --> T[Шаблоны / Bootstrap 5]
    D --> A[REST API /api/]
    A --> JWT[JWT-аутентификация]
    D --> PG[(PostgreSQL)]
    D --> R[(Redis<br/>кэш)]
    D -->|задачи| RQ[[Redis<br/>брокер]]
    RQ --> W[Celery Worker]
    BE[Celery Beat] -->|расписание| RQ
    W --> SMTP[Email]
```

## Быстрый старт (Docker)

```bash
git clone https://github.com/An2rei-84/DiaMed.git
cd DiaMed
cp .env.example .env
docker compose up --build
```

Сайт: http://localhost:8000 · Админка: http://localhost:8000/admin · Swagger: http://localhost:8000/api/docs/

Создание суперпользователя:

```bash
docker compose exec web python manage.py createsuperuser
```

## Локальный запуск без Docker

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate --settings=diamed.settings_local
python manage.py runserver --settings=diamed.settings_local
```

`settings_local.py` использует SQLite и выполняет Celery-задачи синхронно — PostgreSQL и Redis
для разработки не нужны.

## REST API

Документация: `/api/docs/` (Swagger UI), `/api/redoc/`, схема: `/api/schema/`.

| Метод | Эндпоинт | Описание | Доступ |
|-------|----------|----------|--------|
| POST | `/api/auth/token/` | Получение JWT (access + refresh) | публичный |
| POST | `/api/auth/token/refresh/` | Обновление access-токена | публичный |
| GET | `/api/categories/` | Категории услуг | публичный |
| GET | `/api/services/` | Услуги: фильтры, поиск, сортировка | публичный |
| GET | `/api/services/{slug}/` | Детали услуги | публичный |
| GET | `/api/appointments/available-slots/` | Свободные слоты (`?service=&date=`) | публичный |
| GET | `/api/appointments/` | Свои записи | JWT |
| POST | `/api/appointments/` | Создание записи (проверка слота) | JWT |
| GET | `/api/appointments/{id}/` | Детали записи с результатом | JWT, владелец |
| POST | `/api/appointments/{id}/cancel/` | Отмена записи | JWT, владелец |
| GET | `/api/appointments/{id}/result/` | Результат диагностики | JWT, владелец |

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `SECRET_KEY` | — | Ключ Django (обязателен в продакшене) |
| `DEBUG` | `True` | Режим отладки |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Домены через запятую |
| `CSRF_TRUSTED_ORIGINS` | — | Источники для CSRF (`https://example.com`) |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | `diamed` / `diamed` / `diamed123` | Подключение к PostgreSQL |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `localhost` / `5432` | Хост и порт PostgreSQL |
| `REDIS_URL` | `redis://localhost:6379/0` | Брокер Celery и кэш |
| `USE_REDIS_CACHE` | `False` | Включить Redis как кэш Django |
| `EMAIL_BACKEND` | `console` | `console` (вывод в консоль) или `smtp` |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | — | Параметры SMTP |
| `DIAMED_IMAGE` | — | Образ для серверного деплоя (только на сервере) |

## Модели данных

| Приложение | Модели |
|------------|--------|
| `core` | `ContactForm` — сообщения формы обратной связи |
| `about` | `CompanyHistory`, `TeamMember`, `CompanyValue` |
| `services` | `ServiceCategory`, `Service` |
| `contacts` | `Contact` |
| `users` | `UserProfile`, `Appointment` (записи на приём), `DiagnosticResult` |

## Тестирование

139 тестов, покрытие кода 99%.

```bash
make test          # все тесты
make test-cov      # тесты с отчётом покрытия
make test-one module=api tests=TestServiceAPI   # конкретный набор
```

Структура тестов:

```
apps/
├── conftest.py               # Общие фикстуры
├── core/tests.py             # Главная страница, форма связи
├── about/tests.py            # О компании
├── services/tests.py         # Услуги
├── contacts/tests.py         # Контакты
├── users/
│   ├── tests.py              # Личный кабинет, авторизация
│   └── test_tasks.py         # Celery-задачи
└── api/tests/                # REST API: услуги, записи, слоты, JWT
```

## CI/CD

GitHub Actions: **линтинг** (flake8, isort, black) → **тесты** (pytest + PostgreSQL, отчёт
покрытия в Codecov) → **сборка** Docker-образа и публикация в Docker Hub (push в `main`) →
**деплой** на сервер по SSH (`docker compose pull && up -d`, миграции, сбор статики).

Pre-commit хуки для локальной проверки:

```bash
make install            # установка hooks
pre-commit run --all-files
```

## Деплой на сервер

Образ публикуется в Docker Hub (`<username>/diamed:latest`). На сервере используется
`docker-compose.prod.yml` (db, redis, web, celery, celery-beat) — см. `docs/CI_CD.md`.

## Лицензия

MIT License

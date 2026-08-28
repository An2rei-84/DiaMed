# DiaMed - Сайт медицинской диагностики

Современный веб-сайт для компании медицинской диагностики с личным кабинетом пациентов и административной панелью

## Описание проекта

DiaMed — это полноценный веб-сайт для медицинского диагностического центра, включающий:

- 📄 Главная страница с информацией о компании и услугах
- 👨‍⚕️ Раздел "О компании" с историей и командой врачей
- 🏥 Каталог медицинских услуг с ценами
- 📞 Контактная информация и карта проезда
- 👤 Личный кабинет пациента с записью на приём и результатами
- 🔐 Админ-панель для управления контентом

## Технологии

- **Backend**: Django 4.2 LTS
- **Frontend**: Bootstrap 5
- **Database**: PostgreSQL 15
- **Containers**: Docker & Docker Compose
- **WSGI Server**: Gunicorn

## Структура проекта

```
DiaMed/
├── diamed/                 # Главный проект Django
│   ├── settings.py         # Настройки
│   ├── settings_local.py   # Локальные настройки (SQLite)
│   ├── urls.py             # Главный роутер
│   ├── wsgi.py             # WSGI конфигурация
│   └── asgi.py             # ASGI конфигурация
├── apps/
│   ├── core/               # Главная страница, форма связи
│   ├── about/              # О компании (история, команда, ценности)
│   ├── services/           # Услуги и категории
│   ├── contacts/           # Контакты с Яндекс.Картами
│   └── users/              # Личный кабинет, авторизация, результаты
├── static/                 # Статические файлы
├── templates/              # HTML шаблоны
├── media/                  # Медиа файлы
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Установка и запуск

### Требования

- Docker
- Docker Compose

### Запуск через Docker (рекомендуется)

1. **Клонируйте репозиторий**
   ```bash
   git clone <repository-url>
   cd DiaMed
   ```

2. **Создайте файл `.env`**
   ```bash
   cp .env.example .env
   ```
   При необходимости измените настройки в `.env`.

3. **Запустите контейнеры**
   ```bash
   docker-compose up --build
   ```

4. **Создайте суперпользователя** (в новом терминале)
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Откройте сайт**
   - Сайт: http://localhost:8000
   - Админка: http://localhost:8000/admin

### Полезные команды Docker

```bash
# Остановка контейнеров
docker-compose down

# Перезапуск контейнеров
docker-compose restart

# Просмотр логов
docker-compose logs -f web

# Выполнение миграций
docker-compose exec web python manage.py migrate

# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser

# Сбор статических файлов
docker-compose exec web python manage.py collectstatic

# Открыть shell в контейнере
docker-compose exec web bash
```

## Разработка без Docker

### Локальная установка

1. **Создайте виртуальное окружение**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate     # Windows
   # или
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Установите зависимости**
   ```bash
   pip install Django==4.2.16 django-bootstrap5 python-dotenv Pillow
   ```

3. **Запуск с SQLite (без PostgreSQL)**
   ```bash
   python manage.py migrate --settings=diamed.settings_local
   python manage.py createsuperuser --settings=diamed.settings_local
   python manage.py runserver --settings=diamed.settings_local
   ```

4. **Запуск с PostgreSQL**
   - Установите PostgreSQL
   - Создайте базу данных `diamed`
   - Запустите миграции и сервер как обычно

## Использование

### Личный кабинет

1. Зарегистрируйтесь на сайте или войдите в существующий аккаунт
2. Заполните профиль в личном кабинете
3. Запишитесь на приём через форму
4. Просматривайте историю записей и результаты диагностики

### Админ-панель

1. Войдите в админку через `/admin`
2. **Управление пользователями** — редактирование профилей
3. **Управление услугами** — создание категорий и услуг
4. **Управление записями** — изменение статусов, добавление результатов
5. **Управление контентом** — история компании, команда, контакты

## Модели данных

### Core
- `ContactForm` — Сообщения из формы обратной связи

### About
- `CompanyHistory` — История компании
- `TeamMember` — Сотрудники (врачи)
- `CompanyValue` — Ценности компании

### Services
- `ServiceCategory` — Категории медицинских услуг
- `Service` — Медицинские услуги с ценами и описаниями

### Contacts
- `Contact` — Контактная информация (адрес, телефоны, карта)

### Users
- `UserProfile` — Профиль пользователя
- `Appointment` — Записи на приём
- `DiagnosticResult` — Результаты диагностики (заключения, рекомендации)

## Код стандарты

- Код соответствует **PEP 8**
- Доктрины моделей краткие и на **русском**
- Названия моделей в `CamelCase`
- Названия полей в `snake_case`

## Тестирование

Проект включает полный набор тестов для всех модулей.

### Запуск тестов


```bash
# Все тесты
make test

# С покрытием
make test-cov

# Конкретный тест
make test-one module=core tests=TestCoreViews
```

### Структура тестов

```
apps/
├── conftest.py           # Общие фикстуры
├── core/tests.py         # Тесты core модуля
├── about/tests.py        # Тесты about модуля
├── services/tests.py    # Тесты services модуля
├── contacts/tests.py    # Тесты contacts модуля
└── users/tests.py       # Тесты users модуля
```

### Покрытие тестами

| Модуль | Покрытие |
|--------|----------|
| core | ✅ Models, Views, Forms, URLs |
| about | ✅ Models, Views, URLs |
| services | ✅ Models, Views, URLs |
| contacts | ✅ Models, Views, URLs |
| users | ✅ Models, Views, Forms, URLs, Auth |

## CI/CD

Проект использует GitHub Actions для автоматической проверки и деплоя.

### Workflow включает:

1. **Линтинг** — проверка кода flake8, isort, black
2. **Тестирование** — запуск тестов с pytest
3. **Покрытие** — генерация отчета о покрытии
4. **Сборка** — создание Docker образа
5. **Деплой** — автоматический деплой на сервер

### Pre-commit hooks

Для локальной проверки перед коммитом:

```bash
# Установка
make install

# Хуки будут автоматически запускаться перед каждым коммитом
```

### Makefile команды

```bash
make help           # Все доступные команды
make lint          # Проверить код
make format        # Отформатировать код
make test          # Запустить тесты
make check         # Линтинг + тесты
make clean         # Очистить временные файлы
```

## Лицензия

MIT License

## Поддержка

Для вопросов и предложений создайте issue в репозитории.

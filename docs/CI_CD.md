# CI/CD Pipeline Documentation

## Обзор

Проект DiaMed использует GitHub Actions для автоматической проверки кода, тестирования и деплоя.

## Структура CI/CD Pipeline

### 1. Линтинг (Job: `lint`)

Проверка кода на соответствие стандартам:
- **Flake8** — проверка PEP 8
- **isort** — проверка порядка импортов
- **black** — проверка форматирования

```bash
# Локальный запуск
make lint
```

### 2. Тестирование (Job: `test`)

Запуск тестов с покрытием:
- **pytest** — тестовый фреймворк
- **pytest-cov** — покрытие кода
- **PostgreSQL** — сервис для тестов

```bash
# Локальный запуск
make test
make test-cov
```

### 3. Сборка (Job: `build`)

Создание Docker образа:
- BuildKit для оптимизированной сборки
- Кэширование слоев
- Публикация в Docker Hub

```bash
# Локальная сборка
make docker-build
```

### 4. Деплой (Job: `deploy`)

Автоматический деплой на сервер:
- SSH подключение
- Pull нового образа
- Миграции и collectstatic

## Secrets (GitHub)

Для работы CI/CD необходимо добавить следующие secrets в репозитории:

| Secret | Описание | Пример |
|--------|----------|--------|
| `DOCKER_USERNAME` | Имя пользователя Docker Hub | `myusername` |
| `DOCKER_PASSWORD` | Токен Docker Hub | `dckr_pat_...` |
| `DEPLOY_HOST` | Адрес сервера | `192.168.1.100` |
| `DEPLOY_USER` | Пользователь SSH | `deploy` |
| `DEPLOY_KEY` | Приватный SSH ключ | `-----BEGIN...` |

### Настройка Docker Hub Token

1. Перейдите на https://hub.docker.com/settings/security
2. Нажмите "New Access Token"
3. Скопируйте токен и добавьте в GitHub Secrets

### Настройка SSH ключа

```bash
# Генерация ключа
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/diamed_deploy

# Добавление публичного ключа на сервер
ssh-copy-id -i ~/.ssh/diamed_deploy.pub deploy@your-server.com

# Приватный ключ добавить в GitHub Secrets (DEPLOY_KEY)
cat ~/.ssh/diamed_deploy
```

## Triggers

Pipeline запускается при:
- Push в ветки `main` и `develop`
- Pull Request в ветки `main` и `develop`

## Pre-commit Hooks

Локальная проверка перед коммитом:

```bash
# Установка
make install

# Ручной запуск всех проверок
pre-commit run --all-files
```

## Makefile Команды

```bash
make help           # Все команды
make install        # Установка зависимостей
make lint          # Проверка кода
make format        # Форматирование
make test          # Тесты
make test-cov       # Тесты с покрытием
make check         # Все проверки
make clean         # Очистка
make docker-build  # Сборка Docker
make docker-up     # Запуск контейнеров
make docker-down   # Остановка контейнеров
```

## Отчеты

### Codecov

Отчеты о покрытии автоматически загружаются на Codecov:
- Добавьте `CODECOV_TOKEN` в Secrets
- Отчеты доступны на https://codecov.io

### HTML отчеты

После запуска `make test-cov`:
```bash
# Открыть отчет
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Troubleshooting

### Тесты падают в CI, но локально работают

Проверьте:
1. Версии зависимостей совпадают
2. Переменные окружения установлены
3. Миграции применены

### Docker push fails

Проверьте:
1. `DOCKER_USERNAME` и `DOCKER_PASSWORD` верны
2. Токен Docker Hub имеет правильные права
3. Имя образа корректно

### Deploy fails

Проверьте:
1. SSH ключ действительный
2. Сервер доступен
3. Docker установлен на сервере
4. `docker-compose.yml` присутствует на сервере

## Локальный CI

Для проверки перед push:

```bash
make ci-local
```

Это запустит все проверки CI локально.

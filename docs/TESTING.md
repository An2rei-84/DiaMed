# Тестирование проекта DiaMed

## Обзор

Проект использует pytest как тестовый фреймворк. Тесты покрывают все основные модули приложения.

## Структура тестов

```
apps/
├── conftest.py           # Общие фикстуры
├── core/tests.py         # Тесты core модуля
├── about/tests.py        # Тесты about модуля
├── services/tests.py    # Тесты services модуля
├── contacts/tests.py    # Тесты contacts модуля
└── users/tests.py       # Тесты users модуля
```

## Общие фикстуры (conftest.py)

Доступные фикстуры для всех тестов:

| Фикстура | Описание |
|----------|----------|
| `user_data` | Данные для создания тестового пользователя |
| `user` | Создаёт тестового пользователя |
| `authenticated_client` | Клиент с аутентифицированным пользователем |
| `admin_user` | Суперпользователь для тестов админки |
| `admin_client` | Клиент с правами администратора |
| `sample_service_category` | Тестовая категория услуг |
| `sample_service` | Тестовая услуга |
| `sample_contact` | Тестовые контакты |

## Запуск тестов

### Все тесты

```bash
# Через Makefile
make test

# Прямой вызов
pytest
```

### С покрытием

```bash
# Через Makefile
make test-cov

# Прямой вызов
pytest --cov=apps --cov-report=html --cov-report=term
```

### Конкретный модуль

```bash
# Тесты core
pytest apps/core/tests.py

# Тесты users
pytest apps/users/tests.py
```

### Конкретный тест

```bash
# Через Makefile
make test-one module=core tests=TestCoreViews::test_index_view

# Прямой вызов
pytest apps/core/tests.py::TestCoreViews::test_index_view
```

### Только медленные тесты

```bash
pytest -m slow
```

### Исключить медленные тесты

```bash
pytest -m "not slow"
```

## Покрытие по модулям

### Core (`apps/core/tests.py`)

- ✅ Модели: ContactForm
- ✅ Views: index, contact_form_submit
- ✅ Forms: ContactForm
- ✅ URLs

### About (`apps/about/tests.py`)

- ✅ Модели: CompanyHistory, TeamMember, CompanyValue
- ✅ Views: about_index
- ✅ URLs

### Services (`apps/services/tests.py`)

- ✅ Модели: ServiceCategory, Service
- ✅ Views: services_list, service_detail
- ✅ URLs

### Contacts (`apps/contacts/tests.py`)

- ✅ Модели: Contact
- ✅ Views: contacts_index
- ✅ URLs

### Users (`apps/users/tests.py`)

- ✅ Модели: UserProfile, Appointment, DiagnosticResult
- ✅ Views: register, login, logout, dashboard, profile_edit, appointment_create
- ✅ Forms: UserRegisterForm, UserLoginForm, UserProfileForm, AppointmentForm
- ✅ URLs

## Написание тестов

### Шаблон теста

```python
"""Тесты для модуля."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestModelExample:
    """Тесты модели."""

    def test_create_model(self):
        """Тест создания."""
        # Arrange
        # Act
        # Assert
        pass


@pytest.mark.django_db
class TestViewExample:
    """Тесты views."""

    def test_view_get(self, client):
        """Тест GET запроса."""
        response = client.get(reverse('module:view'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestFormExample:
    """Тесты форм."""

    def test_form_valid(self):
        """Тест валидной формы."""
        from apps.module.forms import FormName
        form = FormName(data={...})
        assert form.is_valid()
```

### Маркеры

```python
@pytest.mark.slow
def test_slow_operation():
    """Медленный тест."""
    pass

@pytest.mark.integration
def test_integration_test():
    """Интеграционный тест."""
    pass
```

## CI/CD

Тесты автоматически запускаются в CI/CD pipeline:

```yaml
# .github/workflows/ci.yml
test:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:15
  steps:
    - name: Запуск тестов с pytest
      run: pytest --cov=apps --cov-report=xml
```

## Troubleshooting

### Тесты падают с ошибкой базы данных

```bash
# Применить миграции
python manage.py migrate

# Или использовать pytest-django (автоматически создает БД)
pytest --create-db
```

### Ошибка "No module named 'pytest'"

```bash
# Установить зависимости
pip install -r requirements.txt
```

### Тесты работают, но покрытие 0%

```bash
# Убедитесь что pytest-cov установлен
pip install pytest-cov

# Проверьте конфигурацию в pytest.ini
```

## Локальный запуск CI

Для проверки перед push:

```bash
make ci-local
```

Это запустит линтинг и тесты как в CI.

## Отчеты

### Текстовый отчет

```bash
pytest --cov=apps --cov-report=term
```

### HTML отчет

```bash
pytest --cov=apps --cov-report=html
open htmlcov/index.html
```

### XML отчет (для CI)

```bash
pytest --cov=apps --cov-report=xml
```

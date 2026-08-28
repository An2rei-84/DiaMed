# Makefile для проекта DiaMed
# Удобные команды для разработки, тестирования и деплоя

.PHONY: help install migrate test lint format clean docker-build docker-up docker-down

# ==================== Основные команды ====================
help: ## Показать эту справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install pre-commit
	pre-commit install

migrate: ## Применить миграции базы данных
	python manage.py migrate

createsuperuser: ## Создать суперпользователя
	python manage.py createsuperuser

collectstatic: ## Собрать статические файлы
	python manage.py collectstatic --noinput

run: ## Запустить сервер разработки
	python manage.py runserver

run-local: ## Запустить с локальными настройками (SQLite)
	python manage.py runserver --settings=diamed.settings_local

# ==================== Тестирование ====================
test: ## Запустить все тесты
	pytest

test-cov: ## Запустить тесты с отчетом о покрытии
	pytest --cov=apps --cov-report=html --cov-report=term
	@echo "\nОтчет о покрытии: htmlcov/index.html"

test-verbose: ## Запустить тесты с подробным выводом
	pytest -v -s

test-one: ## Запустить конкретный тест (использование: make test-one module=core tests=TestCoreViews)
	pytest apps/$(module)/tests.py::$(tests) -v

# ==================== Линтинг и форматирование ====================
lint: ## Проверить код линтерами
	@echo "Проверка Flake8..."
	flake8 apps diamed --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 apps diamed --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
	@echo "Проверка isort..."
	isort --check-only --profile black apps diamed
	@echo "Проверка black..."
	black --check apps diamed

format: ## Отформатировать код
	@echo "Форматирование isort..."
	isort --profile black apps diamed
	@echo "Форматирование black..."
	black apps diamed

check: lint test ## Проверить код и запустить тесты

# ==================== Docker ====================
docker-build: ## Собрать Docker образы
	docker-compose build

docker-up: ## Запустить контейнеры
	docker-compose up -d

docker-down: ## Остановить контейнеры
	docker-compose down

docker-logs: ## Показать логи
	docker-compose logs -f web

docker-shell: ## Открыть shell в контейнере
	docker-compose exec web bash

docker-migrate: ## Применить миграции в Docker
	docker-compose exec web python manage.py migrate

docker-test: ## Запустить тесты в Docker
	docker-compose exec web pytest

docker-create-superuser: ## Создать суперпользователя в Docker
	docker-compose exec web python manage.py createsuperuser

# ==================== Очистка ====================
clean: ## Очистить временные файлы
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	rm -rf staticfiles/ 2>/dev/null || true

clean-all: clean ## Глубокая очистка
	rm -rf .venv/ 2>/dev/null || true
	rm -rf *.egg-info/ 2>/dev/null || true
	docker-compose down -v

# ==================== CI/CD ====================
ci-local: ## Запустить локально CI проверки
	@echo "Запуск линтеров..."
	$(MAKE) lint
	@echo "Запуск тестов..."
	$(MAKE) test
	@echo "✅ Все проверки пройдены!"

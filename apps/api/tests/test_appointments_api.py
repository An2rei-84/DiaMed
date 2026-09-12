"""Тесты API записей на приём."""

from datetime import time

import pytest

from apps.users.models import Appointment

API_LIST = "/api/appointments/"


@pytest.mark.django_db
class TestAppointmentCreateAPI:
    """Создание записи через POST /api/appointments/."""

    def test_create_success(self, auth_api_client, user, sample_service, tomorrow):
        """Валидная запись создаётся и привязывается к текущему пользователю."""
        response = auth_api_client.post(
            API_LIST,
            {"service": sample_service.pk, "date": str(tomorrow), "time": "11:00"},
            format="json",
        )

        assert response.status_code == 201
        appointment = Appointment.objects.get(pk=response.data["id"])
        assert appointment.user == user
        assert appointment.status == "pending"

    def test_create_anonymous_forbidden(self, api_client, sample_service, tomorrow):
        """Анонимный запрос возвращает 401."""
        response = api_client.post(
            API_LIST,
            {"service": sample_service.pk, "date": str(tomorrow), "time": "11:00"},
            format="json",
        )

        assert response.status_code == 401

    def test_create_past_date_rejected(self, auth_api_client, sample_service):
        """Запись на прошедшую дату отклоняется."""
        response = auth_api_client.post(
            API_LIST,
            {"service": sample_service.pk, "date": "2020-01-01", "time": "11:00"},
            format="json",
        )

        assert response.status_code == 400
        assert "прошедшую дату" in str(response.data)

    def test_create_busy_slot_rejected(self, auth_api_client, sample_service, tomorrow):
        """Запись на занятый слот отклоняется."""
        auth_api_client.post(
            API_LIST,
            {"service": sample_service.pk, "date": str(tomorrow), "time": "12:00"},
            format="json",
        )
        response = auth_api_client.post(
            API_LIST,
            {"service": sample_service.pk, "date": str(tomorrow), "time": "12:00"},
            format="json",
        )

        assert response.status_code == 400
        assert "time" in response.data

    def test_create_out_of_work_hours_rejected(self, auth_api_client, sample_service, tomorrow):
        """Слот вне рабочих часов (21:00) отклоняется."""
        response = auth_api_client.post(
            API_LIST,
            {"service": sample_service.pk, "date": str(tomorrow), "time": "21:00"},
            format="json",
        )

        assert response.status_code == 400

    def test_create_inactive_service_rejected(self, auth_api_client, inactive_service, tomorrow):
        """Запись на неактивную услугу отклоняется."""
        response = auth_api_client.post(
            API_LIST,
            {"service": inactive_service.pk, "date": str(tomorrow), "time": "11:00"},
            format="json",
        )

        assert response.status_code == 400
        assert "service" in response.data


@pytest.mark.django_db
class TestInvalidPkAPI:
    """Некорректные pk из пути — 404, а не 500 (нашёл фаззинг Schemathesis)."""

    HUGE_PK = "2252903082365565796352"  # больше 2^63-1

    def test_detail_huge_pk_404(self, auth_api_client):
        """Вне-диапазонный pk в detail не роняет сервер."""
        response = auth_api_client.get(f"{API_LIST}{self.HUGE_PK}/")

        assert response.status_code == 404

    def test_result_huge_pk_404(self, auth_api_client):
        """Вне-диапазонный pk в result не роняет сервер."""
        response = auth_api_client.get(f"{API_LIST}{self.HUGE_PK}/result/")

        assert response.status_code == 404

    def test_cancel_huge_pk_404(self, auth_api_client):
        """Вне-диапазонный pk в cancel не роняет сервер."""
        response = auth_api_client.post(f"{API_LIST}{self.HUGE_PK}/cancel/")

        assert response.status_code == 404

    def test_non_numeric_pk_404(self, auth_api_client):
        """Нечисловой pk отсекается роутингом."""
        response = auth_api_client.get(f"{API_LIST}not-a-number/")

        assert response.status_code == 404


@pytest.mark.django_db
class TestAppointmentRaceConditionAPI:
    """Двойная запись при гонке: UniqueConstraint в БД + IntegrityError → 400."""

    def test_slot_taken_between_validation_and_save(self, auth_api_client, other_user, sample_service, tomorrow, monkeypatch):
        """Гонка: слот занял другой пациент после проверки — 400 с пояснением, не 500."""
        Appointment.objects.create(user=other_user, service=sample_service, date=tomorrow, time=time(10, 0))
        # Валидация «успела» пройти до появления брони: слот считался свободным
        monkeypatch.setattr("apps.api.serializers.get_available_slots", lambda *args, **kwargs: ["10:00"])

        response = auth_api_client.post(
            API_LIST,
            {"service": sample_service.pk, "date": str(tomorrow), "time": "10:00"},
            format="json",
        )

        assert response.status_code == 400
        assert "только что заняли" in str(response.data)

    def test_rebooking_after_cancel_success(self, auth_api_client, user, sample_service, tomorrow):
        """После отмены записи слот снова доступен (констрейнт учитывает только активные)."""
        Appointment.objects.create(user=user, service=sample_service, date=tomorrow, time=time(10, 0), status="cancelled")

        response = auth_api_client.post(
            API_LIST,
            {"service": sample_service.pk, "date": str(tomorrow), "time": "10:00"},
            format="json",
        )

        assert response.status_code == 201


@pytest.mark.django_db
class TestAppointmentListDetailAPI:
    """Чтение записей через GET /api/appointments/."""

    def test_list_only_own_appointments(self, auth_api_client, user, other_user, appointment, sample_service, tomorrow):
        """В списке только записи текущего пользователя."""
        Appointment.objects.create(
            user=other_user,
            service=sample_service,
            date=tomorrow,
            time=time(14, 0),
        )

        response = auth_api_client.get(API_LIST)

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["time"] == "10:00:00"

    def test_detail_own(self, auth_api_client, appointment):
        """Владелец видит свою запись."""
        response = auth_api_client.get(f"{API_LIST}{appointment.pk}/")

        assert response.status_code == 200
        assert response.data["service_slug"] == "analiz-krovi"
        assert response.data["status_display"] == "Ожидает"

    def test_detail_other_user_404(self, api_client, other_user, appointment):
        """Чужая запись недоступна (фильтрация по пользователю)."""
        api_client.force_authenticate(user=other_user)
        response = api_client.get(f"{API_LIST}{appointment.pk}/")

        assert response.status_code == 404

    def test_update_not_allowed(self, auth_api_client, appointment):
        """Изменение записи не поддерживается (405)."""
        response = auth_api_client.patch(f"{API_LIST}{appointment.pk}/", {})

        assert response.status_code == 405

    def test_delete_not_allowed(self, auth_api_client, appointment):
        """Удаление записи не поддерживается (405)."""
        response = auth_api_client.delete(f"{API_LIST}{appointment.pk}/")

        assert response.status_code == 405


@pytest.mark.django_db
class TestAppointmentCancelAPI:
    """Отмена записи через POST /api/appointments/{id}/cancel/."""

    def test_cancel_pending(self, auth_api_client, appointment):
        """Ожидающая запись отменяется владельцем."""
        response = auth_api_client.post(f"{API_LIST}{appointment.pk}/cancel/")

        assert response.status_code == 200
        assert response.data["status"] == "cancelled"

    def test_cancel_already_cancelled(self, auth_api_client, appointment):
        """Повторная отмена возвращает 400."""
        appointment.status = "cancelled"
        appointment.save()

        response = auth_api_client.post(f"{API_LIST}{appointment.pk}/cancel/")

        assert response.status_code == 400

    def test_cancel_other_user_404(self, api_client, other_user, appointment):
        """Чужую запись отменить нельзя."""
        api_client.force_authenticate(user=other_user)
        response = api_client.post(f"{API_LIST}{appointment.pk}/cancel/")

        assert response.status_code == 404


@pytest.mark.django_db
class TestAppointmentResultAPI:
    """Результат диагностики через GET /api/appointments/{id}/result/."""

    def test_result_not_ready(self, auth_api_client, appointment):
        """Если результата нет — 404 с пояснением."""
        response = auth_api_client.get(f"{API_LIST}{appointment.pk}/result/")

        assert response.status_code == 404
        assert "не готов" in response.data["detail"]

    def test_result_ready(self, auth_api_client, appointment, diagnostic_result):
        """Готовый результат возвращается владельцу."""
        response = auth_api_client.get(f"{API_LIST}{appointment.pk}/result/")

        assert response.status_code == 200
        assert response.data["conclusion"] == "Показатели в пределах нормы"
        assert response.data["doctor"] == "Иванов И. И."

    def test_result_included_in_detail(self, auth_api_client, appointment, diagnostic_result):
        """Результат вкладывается в ответ детальной записи."""
        response = auth_api_client.get(f"{API_LIST}{appointment.pk}/")

        assert response.status_code == 200
        assert response.data["result"]["is_normal"] is True

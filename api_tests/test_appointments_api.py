"""Black-box тесты записи на приём (/api/appointments/)."""

import requests

QA_USERNAME = "qa_api"
QA_PASSWORD = "qa_pass_123"
SERVICE_NAME = "Анализ крови"


def _create(base_url, headers, service_pk, appointment_date, appointment_time, notes=""):
    """Создаёт запись через API (типовой запрос)."""
    return requests.post(
        f"{base_url}/api/appointments/",
        headers=headers,
        json={"service": service_pk, "date": str(appointment_date), "time": appointment_time, "notes": notes},
        timeout=10,
    )


class TestAvailableSlotsAPI:
    """Публичный эндпоинт свободных слотов."""

    def test_missing_params_400(self, base_url):
        """Без параметров — 400 с подсказкой."""
        response = requests.get(f"{base_url}/api/appointments/available-slots/", timeout=10)

        assert response.status_code == 400
        assert "service" in response.json()["detail"]

    def test_unknown_service_404(self, base_url, tomorrow):
        """Неизвестная услуга — 404."""
        response = requests.get(
            f"{base_url}/api/appointments/available-slots/",
            params={"service": "net-takoy", "date": str(tomorrow)},
            timeout=10,
        )

        assert response.status_code == 404

    def test_bad_date_format_400(self, base_url):
        """Дата не в формате YYYY-MM-DD — 400."""
        response = requests.get(
            f"{base_url}/api/appointments/available-slots/",
            params={"service": "analiz-krovi", "date": "01.02.2030"},
            timeout=10,
        )

        assert response.status_code == 400

    def test_slots_returned(self, base_url, tomorrow):
        """Рабочий день отдаёт слоты с 08:00 по 19:30."""
        response = requests.get(
            f"{base_url}/api/appointments/available-slots/",
            params={"service": "analiz-krovi", "date": "2030-07-07"},
            timeout=10,
        )

        assert response.status_code == 200
        slots = response.json()["available_slots"]
        assert slots[0] == "08:00"
        assert slots[-1] == "19:30"


class TestAppointmentCreateAPI:
    """Создание записи: позитивные и негативные сценарии."""

    def test_create_anonymous_401(self, base_url, service_pk, tomorrow):
        """Анонимное создание — 401."""
        response = _create(base_url, {}, service_pk, tomorrow, "10:00")

        assert response.status_code == 401

    def test_create_success(self, base_url, auth_headers, service_pk, tomorrow, free_slots):
        """Валидная запись создаётся; detail показывает slug услуги и статус «Ожидает»."""
        created = _create(base_url, auth_headers, service_pk, tomorrow, free_slots[0])

        assert created.status_code == 201, created.text
        assert created.json()["service"] == service_pk

        detail = requests.get(f"{base_url}/api/appointments/{created.json()['id']}/", headers=auth_headers, timeout=10).json()
        assert detail["service_slug"] == "analiz-krovi"
        assert detail["status"] == "pending"

    def test_create_past_date_400(self, base_url, auth_headers, service_pk):
        """Прошедшая дата отклоняется с внятным сообщением."""
        response = _create(base_url, auth_headers, service_pk, "2020-01-01", "10:00")

        assert response.status_code == 400
        assert "прошедшую дату" in str(response.json())

    def test_create_out_of_hours_400(self, base_url, auth_headers, service_pk, tomorrow):
        """Слот вне рабочих часов отклоняется полем time."""
        response = _create(base_url, auth_headers, service_pk, tomorrow, "21:00")

        assert response.status_code == 400
        assert "time" in response.json()

    def test_create_busy_slot_400(self, base_url, auth_headers, service_pk, tomorrow, free_slots):
        """Повторная запись на занятый слот отклоняется."""
        slot = free_slots[0]
        first = _create(base_url, auth_headers, service_pk, tomorrow, slot)
        assert first.status_code == 201

        second = _create(base_url, auth_headers, service_pk, tomorrow, slot)

        assert second.status_code == 400
        assert "time" in second.json()


class TestAppointmentReadAPI:
    """Чтение и изоляция данных между пользователями."""

    def test_list_and_pagination_shape(self, base_url, auth_headers):
        """Список своих записей в формате пагинации, включая seeded завершённую."""
        response = requests.get(f"{base_url}/api/appointments/", headers=auth_headers, timeout=10)

        assert response.status_code == 200
        body = response.json()
        assert {"count", "next", "previous", "results"} <= set(body)
        assert body["count"] >= 1

    def test_detail_own(self, base_url, auth_headers, service_pk, free_slots):
        """Владелец видит свою запись."""
        created = _create(base_url, auth_headers, service_pk, "2030-05-05", free_slots[0]).json()

        response = requests.get(f"{base_url}/api/appointments/{created['id']}/", headers=auth_headers, timeout=10)

        assert response.status_code == 200
        assert response.json()["service_slug"] == "analiz-krovi"

    def test_detail_other_user_404(self, base_url, auth_headers, auth_headers2, service_pk, free_slots):
        """Чужая запись не видна (404, а не 403 — без раскрытия существования)."""
        created = _create(base_url, auth_headers, service_pk, "2030-05-06", free_slots[1]).json()

        response = requests.get(f"{base_url}/api/appointments/{created['id']}/", headers=auth_headers2, timeout=10)

        assert response.status_code == 404

    def test_detail_unknown_id_404(self, base_url, auth_headers):
        """Несуществующий id — 404."""
        response = requests.get(f"{base_url}/api/appointments/999999/", headers=auth_headers, timeout=10)

        assert response.status_code == 404

    def test_update_not_allowed_405(self, base_url, auth_headers):
        """PATCH не поддерживается."""
        response = requests.patch(f"{base_url}/api/appointments/1/", headers=auth_headers, json={}, timeout=10)

        assert response.status_code == 405

    def test_delete_not_allowed_405(self, base_url, auth_headers):
        """DELETE не поддерживается."""
        response = requests.delete(f"{base_url}/api/appointments/1/", headers=auth_headers, timeout=10)

        assert response.status_code == 405


class TestAppointmentCancelAPI:
    """Отмена записи и освобождение слота."""

    def test_cancel_flow_and_slot_released(self, base_url, auth_headers, service_pk, tomorrow, free_slots):
        """Отмена: pending → cancelled, слот снова в available-slots."""
        slot = free_slots[1]
        created = _create(base_url, auth_headers, service_pk, tomorrow, slot).json()

        response = requests.post(f"{base_url}/api/appointments/{created['id']}/cancel/", headers=auth_headers, timeout=10)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

        slots = requests.get(
            f"{base_url}/api/appointments/available-slots/",
            params={"service": "analiz-krovi", "date": str(tomorrow)},
            timeout=10,
        ).json()["available_slots"]
        assert slot in slots

    def test_cancel_twice_400(self, base_url, auth_headers, service_pk, tomorrow, free_slots):
        """Повторная отмена уже отменённой — 400."""
        created = _create(base_url, auth_headers, service_pk, tomorrow, free_slots[2]).json()
        requests.post(f"{base_url}/api/appointments/{created['id']}/cancel/", headers=auth_headers, timeout=10)

        response = requests.post(f"{base_url}/api/appointments/{created['id']}/cancel/", headers=auth_headers, timeout=10)

        assert response.status_code == 400

    def test_cancel_other_user_404(self, base_url, auth_headers, auth_headers2, service_pk, tomorrow, free_slots):
        """Чужую запись отменить нельзя — 404."""
        created = _create(base_url, auth_headers, service_pk, tomorrow, free_slots[3]).json()

        response = requests.post(f"{base_url}/api/appointments/{created['id']}/cancel/", headers=auth_headers2, timeout=10)

        assert response.status_code == 404


class TestAppointmentResultAPI:
    """Результаты диагностики по записи."""

    def _find_completed(self, base_url, headers):
        """Ищет seeded завершённую запись основного пользователя."""
        results = requests.get(f"{base_url}/api/appointments/", headers=headers, timeout=10).json()["results"]
        return next(item for item in results if item["status"] == "completed")

    def test_result_ready(self, base_url, auth_headers):
        """Завершённая запись с результатом отдаёт заключение."""
        completed = self._find_completed(base_url, auth_headers)

        response = requests.get(f"{base_url}/api/appointments/{completed['id']}/result/", headers=auth_headers, timeout=10)

        assert response.status_code == 200
        assert response.json()["conclusion"] == "Показатели в пределах нормы"
        assert response.json()["doctor"] == "Иванов И. И."

    def test_result_not_ready_404(self, base_url, auth_headers, service_pk, tomorrow, free_slots):
        """Для свежей записи результата ещё нет — 404."""
        created = _create(base_url, auth_headers, service_pk, tomorrow, free_slots[4]).json()

        response = requests.get(f"{base_url}/api/appointments/{created['id']}/result/", headers=auth_headers, timeout=10)

        assert response.status_code == 404
        assert "не готов" in response.json()["detail"]

    def test_result_other_user_404(self, base_url, auth_headers, auth_headers2):
        """Результат чужой записи не отдаётся."""
        completed = self._find_completed(base_url, auth_headers)

        response = requests.get(f"{base_url}/api/appointments/{completed['id']}/result/", headers=auth_headers2, timeout=10)

        assert response.status_code == 404

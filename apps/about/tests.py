"""Тесты для about приложения."""

from django.urls import reverse

import pytest

from apps.about.models import CompanyHistory, CompanyValue, TeamMember


@pytest.mark.django_db
class TestCompanyHistoryModel:
    """Тесты модели CompanyHistory."""

    def test_create_company_history(self):
        """Тест создания события истории."""
        history = CompanyHistory.objects.create(
            year=2020, title="Открытие первой клиники", description="Открыли первую клинику в центре Москвы"
        )
        assert history.year == 2020
        assert history.title == "Открытие первой клиники"
        assert history.description == "Открыли первую клинику в центре Москвы"

    def test_company_history_str(self):
        """Тест строкового представления."""
        history = CompanyHistory.objects.create(year=2021, title="Расширение", description="Открыли филиалы")
        str_repr = str(history)
        assert "2021" in str_repr
        assert "Расширение" in str_repr

    def test_company_history_ordering(self):
        """Тест сортировки истории."""
        CompanyHistory.objects.create(year=2022, title="Событие 2", description="...")
        CompanyHistory.objects.create(year=2020, title="Событие 1", description="...")
        histories = list(CompanyHistory.objects.all())
        assert histories[0].year == 2020
        assert histories[1].year == 2022


@pytest.mark.django_db
class TestTeamMemberModel:
    """Тесты модели TeamMember."""

    def test_create_team_member(self):
        """Тест создания сотрудника."""
        member = TeamMember.objects.create(
            name="Иванов Иван Иванович",
            position="Врач-терапевт",
            speciality="Терапия",
            experience=10,
            description="Опытный врач",
        )
        assert member.name == "Иванов Иван Иванович"
        assert member.position == "Врач-терапевт"
        assert member.experience == 10
        assert member.is_active is True

    def test_team_member_str(self):
        """Тест строкового представления."""
        member = TeamMember.objects.create(name="Петров Петр", position="Хирург", speciality="Хирургия", experience=5)
        str_repr = str(member)
        assert "Петров Петр" in str_repr
        assert "Хирург" in str_repr

    def test_team_member_ordering(self):
        """Тест сортировки сотрудников."""
        TeamMember.objects.create(name="Иванов Иван", position="Врач", speciality="Терапия", experience=10)
        TeamMember.objects.create(name="Алексеев Алексей", position="Врач", speciality="Хирургия", experience=5)
        members = list(TeamMember.objects.all())
        # Должны быть отсортированы по имени
        assert members[0].name == "Алексеев Алексей"
        assert members[1].name == "Иванов Иван"

    def test_team_member_active_filter(self):
        """Тест фильтрации активных сотрудников."""
        TeamMember.objects.create(name="Активный врач", position="Врач", speciality="Терапия", experience=10, is_active=True)
        TeamMember.objects.create(name="Неактивный врач", position="Врач", speciality="Хирургия", experience=5, is_active=False)
        active_members = TeamMember.objects.filter(is_active=True)
        assert active_members.count() == 1
        assert active_members.first().name == "Активный врач"


@pytest.mark.django_db
class TestCompanyValueModel:
    """Тесты модели CompanyValue."""

    def test_create_company_value(self):
        """Тест создания ценности."""
        value = CompanyValue.objects.create(title="Качество", description="Мы обеспечиваем высокое качество услуг")
        assert value.title == "Качество"
        assert value.description == "Мы обеспечиваем высокое качество услуг"

    def test_company_value_with_icon(self):
        """Тест создания ценности с иконкой."""
        value = CompanyValue.objects.create(title="Забота", description="Заботимся о пациентах", icon="bi-heart")
        assert value.icon == "bi-heart"

    def test_company_value_str(self):
        """Тест строкового представления."""
        value = CompanyValue.objects.create(title="Профессионализм", description="Только профессионалы")
        assert str(value) == "Профессионализм"


@pytest.mark.django_db
class TestAboutViews:
    """Тесты views about приложения."""

    def test_about_view(self, client):
        """Тест страницы 'О нас'."""
        response = client.get(reverse("about:index"))
        assert response.status_code == 200
        assert "histories" in response.context
        assert "team" in response.context
        assert "values" in response.context

    def test_about_view_with_data(self, client):
        """Тест страницы с данными."""
        # Создаем тестовые данные
        CompanyHistory.objects.create(year=2020, title="Событие", description="Описание")
        TeamMember.objects.create(name="Врач", position="Доктор", speciality="Терапия", experience=10, is_active=True)
        CompanyValue.objects.create(title="Ценность", description="Описание ценности")

        response = client.get(reverse("about:index"))
        assert response.status_code == 200
        assert len(response.context["histories"]) == 1
        assert len(response.context["team"]) == 1
        assert len(response.context["values"]) == 1

    def test_about_view_team_only_active(self, client):
        """Тест что выводятся только активные сотрудники."""
        TeamMember.objects.create(name="Активный", position="Врач", speciality="Терапия", experience=10, is_active=True)
        TeamMember.objects.create(name="Неактивный", position="Врач", speciality="Хирургия", experience=5, is_active=False)

        response = client.get(reverse("about:index"))
        assert response.status_code == 200
        assert len(response.context["team"]) == 1
        assert response.context["team"][0].name == "Активный"


@pytest.mark.django_db
class TestAboutUrls:
    """Тесты URL routing about приложения."""

    def test_about_url_resolves(self):
        """Тест разрешения URL страницы 'О нас'."""
        url = reverse("about:index")
        assert url == "/about/"

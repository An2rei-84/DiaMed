"""Сериализаторы API."""

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from apps.services.models import Service, ServiceCategory
from apps.users.models import Appointment, DiagnosticResult
from apps.users.tasks import send_appointment_confirmation

from .services import get_available_slots


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Категория услуг."""

    class Meta:
        """Настройки сериализатора."""

        model = ServiceCategory
        fields = ["id", "name", "slug", "description", "icon"]


class ServiceSerializer(serializers.ModelSerializer):
    """Медицинская услуга."""

    category = serializers.StringRelatedField(read_only=True)
    category_slug = serializers.SlugRelatedField(source="category", slug_field="slug", read_only=True)

    class Meta:
        """Настройки сериализатора."""

        model = Service
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "category_slug",
            "description",
            "price",
            "duration",
            "preparation",
            "image",
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    """Запись на приём: чтение."""

    service = serializers.StringRelatedField(read_only=True)
    service_slug = serializers.SlugRelatedField(source="service", slug_field="slug", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    result = serializers.SerializerMethodField()

    class Meta:
        """Настройки сериализатора."""

        model = Appointment
        fields = [
            "id",
            "service",
            "service_slug",
            "date",
            "time",
            "status",
            "status_display",
            "notes",
            "result",
            "created_at",
            "updated_at",
        ]

    def get_result(self, obj):
        """Возвращает результат диагностики, если он готов."""
        try:
            return DiagnosticResultSerializer(obj.result).data
        except DiagnosticResult.DoesNotExist:
            return None


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Создание записи на приём с проверкой свободных слотов."""

    class Meta:
        """Настройки сериализатора."""

        model = Appointment
        fields = ["id", "service", "date", "time", "notes"]

    def validate_service(self, value):
        """Записаться можно только на активную услугу."""
        if not value.is_active:
            raise serializers.ValidationError("Эта услуга сейчас недоступна для записи.")
        return value

    def validate_date(self, value):
        """Дата приёма не может быть в прошлом."""
        if value < timezone.localdate():
            raise serializers.ValidationError("Нельзя записаться на прошедшую дату.")
        return value

    def validate(self, attrs):
        """Проверяет, что выбранный слот свободен и входит в рабочие часы."""
        slots = get_available_slots(attrs["service"], attrs["date"])
        slot = attrs["time"].strftime("%H:%M")
        if slot not in slots:
            raise serializers.ValidationError({"time": f"Время {slot} занято или вне рабочих часов (8:00–20:00)."})
        return attrs

    def create(self, validated_data):
        """Создаёт запись текущему пользователю и ставит отправку подтверждения."""
        validated_data["user"] = self.context["request"].user
        appointment = super().create(validated_data)
        transaction.on_commit(lambda: send_appointment_confirmation.delay(appointment.pk))
        return appointment


class DiagnosticResultSerializer(serializers.ModelSerializer):
    """Результат диагностики (только чтение)."""

    class Meta:
        """Настройки сериализатора."""

        model = DiagnosticResult
        fields = [
            "id",
            "appointment",
            "conclusion",
            "recommendations",
            "doctor",
            "result_date",
            "attachment",
            "is_normal",
        ]
        read_only_fields = fields

"""Сериализаторы API."""

from django.db import IntegrityError, transaction
from django.utils import timezone

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.services.models import Service, ServiceCategory
from apps.users.models import Appointment, DiagnosticResult
from apps.users.tasks import send_appointment_confirmation

from .services import SLOT_TAKEN_MESSAGE, get_available_slots


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


class AvailableSlotsSerializer(serializers.Serializer):
    """Свободные слоты для услуги на дату."""

    service = serializers.CharField()
    date = serializers.DateField()
    available_slots = serializers.ListField(child=serializers.CharField())


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

    @extend_schema_field(DiagnosticResultSerializer(allow_null=True))
    def get_result(self, obj):
        """Возвращает результат диагностики, если он готов."""
        try:
            return DiagnosticResultSerializer(obj.result).data
        except DiagnosticResult.DoesNotExist:
            return None


class SafePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """PrimaryKeyRelatedField, отвергающий pk вне диапазона bigint.

    Фаззинг (Schemathesis) подсовывает в тело запроса гигантские целые:
    без ограничения они доходят до DB-адаптера и роняют запрос с
    OverflowError → 500. Здесь мусор отсекается на уровне валидации.
    """

    MAX_PK = 10**18  # гарантированно внутри bigint (2^63-1); согласовано с lookup_value_regex во вью

    def to_internal_value(self, data):
        """Проверяет, что pk — целое в разумном диапазоне, до похода в БД."""
        try:
            value = int(data)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data).__name__)
        if not 0 < value <= self.MAX_PK:
            self.fail("does_not_exist", pk_value=data)
        return super().to_internal_value(data)


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Создание записи на приём с проверкой свободных слотов."""

    service = SafePrimaryKeyRelatedField(queryset=Service.objects.all())

    class Meta:
        """Настройки сериализатора."""

        model = Appointment
        fields = ["id", "service", "date", "time", "notes"]
        # Отключаем автогенерацию UniqueTogetherValidator из констрейнта модели:
        # занятость слота проверяет validate() с понятным сообщением, а гонку
        # между проверкой и INSERT закрывает IntegrityError в create()
        validators = []

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
        try:
            with transaction.atomic():
                appointment = super().create(validated_data)
        except IntegrityError:
            # Слот заняли между проверкой validate() и INSERT (гонка) —
            # гарантию даёт UniqueConstraint на уровне БД
            raise serializers.ValidationError({"time": SLOT_TAKEN_MESSAGE})
        transaction.on_commit(lambda: send_appointment_confirmation.delay(appointment.pk))
        return appointment

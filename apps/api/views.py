"""Представления API."""

from datetime import datetime

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.services.models import Service, ServiceCategory
from apps.users.models import Appointment, DiagnosticResult

from .permissions import IsOwner
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    AvailableSlotsSerializer,
    DiagnosticResultSerializer,
    ServiceCategorySerializer,
    ServiceSerializer,
)
from .services import get_available_slots

# pk записи: в схеме объявлен целым числом, иначе drf-spectacular пишет "string",
# фаззер генерирует нечисловой мусор и роутинг его отсекает
ID_PATH_PARAM = OpenApiParameter(name="id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH)


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Категории услуг (только чтение, без пагинации)."""

    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = (AllowAny,)
    lookup_field = "slug"
    pagination_class = None

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                examples=[OpenApiExample("Диагностика", value="diagnostika")],
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        """Детали категории."""
        return super().retrieve(request, *args, **kwargs)


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """Медицинские услуги: список с фильтрами, поиском и сортировкой."""

    queryset = Service.objects.filter(is_active=True).select_related("category")
    serializer_class = ServiceSerializer
    permission_classes = (AllowAny,)
    lookup_field = "slug"
    filterset_fields = ["category__slug"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name"]

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        """Список активных услуг (ответ кэшируется на 5 минут)."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="slug",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                examples=[OpenApiExample("Анализ крови", value="analiz-krovi")],
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        """Детали услуги."""
        return super().retrieve(request, *args, **kwargs)


class AppointmentViewSet(viewsets.ModelViewSet):
    """Записи на приём текущего пользователя."""

    permission_classes = (IsAuthenticated, IsOwner)
    http_method_names = ["get", "post", "head", "options"]
    ordering_fields = ["date", "time", "status"]
    # pk — не более 18 цифр: значения вне диапазона bigint (2^63-1) отсекаются
    # роутингом и дают 404, иначе DB-адаптер падает OverflowError/DataError → 500
    lookup_value_regex = "[0-9]{1,18}"

    def get_queryset(self):
        """Возвращает только записи текущего пользователя."""
        if getattr(self, "swagger_fake_view", False):
            # Генерация OpenAPI-схемы: реального пользователя нет
            return Appointment.objects.none()
        return Appointment.objects.filter(user=self.request.user).select_related("service").order_by("-date", "-time")

    def get_serializer_class(self):
        """При создании записи — сериализатор с валидацией слотов."""
        if self.action == "create":
            return AppointmentCreateSerializer
        return AppointmentSerializer

    @extend_schema(parameters=[ID_PATH_PARAM])
    def retrieve(self, request, *args, **kwargs):
        """Детали записи."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(parameters=[ID_PATH_PARAM], responses=AppointmentSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Отмена записи владельцем (только в статусе pending/confirmed)."""
        appointment = self.get_object()
        if appointment.status not in ("pending", "confirmed"):
            return Response(
                {"detail": "Запись уже завершена или отменена."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = "cancelled"
        appointment.save(update_fields=("status", "updated_at"))
        return Response(AppointmentSerializer(appointment).data)

    @extend_schema(parameters=[ID_PATH_PARAM], responses=DiagnosticResultSerializer)
    @action(detail=True, methods=["get"])
    def result(self, request, pk=None):
        """Результат диагностики по записи."""
        try:
            result = self.get_object().result
        except DiagnosticResult.DoesNotExist:
            return Response(
                {"detail": "Результат пока не готов."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(DiagnosticResultSerializer(result).data)


class AvailableSlotsView(APIView):
    """Свободные слоты записи на приём."""

    permission_classes = (AllowAny,)

    @extend_schema(
        parameters=[
            OpenApiParameter(name="service", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="date", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
        ],
        responses=AvailableSlotsSerializer,
    )
    def get(self, request):
        """Возвращает свободные слоты для услуги и даты.

        Параметры запроса: service (slug услуги) и date (YYYY-MM-DD).
        """
        service_slug = request.query_params.get("service")
        date_str = request.query_params.get("date")
        if not service_slug or not date_str:
            return Response(
                {"detail": "Укажите параметры service и date."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = Service.objects.filter(slug=service_slug, is_active=True).first()
        if service is None:
            return Response({"detail": "Услуга не найдена."}, status=status.HTTP_404_NOT_FOUND)

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "Неверный формат даты, ожидается YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "service": service.slug,
                "date": date_str,
                "available_slots": get_available_slots(service, date),
            }
        )

"""Представления API."""

from datetime import datetime

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

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
    DiagnosticResultSerializer,
    ServiceCategorySerializer,
    ServiceSerializer,
)
from .services import get_available_slots


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Категории услуг (только чтение, без пагинации)."""

    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = (AllowAny,)
    lookup_field = "slug"
    pagination_class = None


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


class AppointmentViewSet(viewsets.ModelViewSet):
    """Записи на приём текущего пользователя."""

    permission_classes = (IsAuthenticated, IsOwner)
    http_method_names = ["get", "post", "head", "options"]
    ordering_fields = ["date", "time", "status"]

    def get_queryset(self):
        """Возвращает только записи текущего пользователя."""
        return Appointment.objects.filter(user=self.request.user).select_related("service").order_by("-date", "-time")

    def get_serializer_class(self):
        """При создании записи — сериализатор с валидацией слотов."""
        if self.action == "create":
            return AppointmentCreateSerializer
        return AppointmentSerializer

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

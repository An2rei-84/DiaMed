"""Маршруты API."""

from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register("categories", views.ServiceCategoryViewSet, basename="category")
router.register("services", views.ServiceViewSet, basename="service")
router.register("appointments", views.AppointmentViewSet, basename="appointment")

urlpatterns = [
    # JWT-аутентификация
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Явные маршруты до роутера: иначе router съедает "available-slots" как pk
    path(
        "appointments/available-slots/",
        views.AvailableSlotsView.as_view(),
        name="available-slots",
    ),
    # OpenAPI-схема и документация
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("", include(router.urls)),
]

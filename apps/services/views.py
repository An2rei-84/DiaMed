"""Views для services приложения."""

from django.shortcuts import get_object_or_404, render

from .models import Service, ServiceCategory


def services_list(request):
    """Список услуг."""

    services = Service.objects.filter(is_active=True).select_related("category")
    categories = ServiceCategory.objects.all()

    category_slug = request.GET.get("category")
    if category_slug:
        services = services.filter(category__slug=category_slug)

    context = {
        "services": services,
        "categories": categories,
        "current_category": category_slug,
    }
    return render(request, "services/list.html", context)


def service_detail(request, slug):
    """Детальная страница услуги."""

    service = get_object_or_404(Service, slug=slug, is_active=True)

    context = {
        "service": service,
    }
    return render(request, "services/detail.html", context)

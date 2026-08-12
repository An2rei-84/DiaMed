"""Views для about приложения."""

from django.shortcuts import render
from .models import CompanyHistory, TeamMember, CompanyValue


def about_index(request):
    """Страница 'О компании'."""

    histories = CompanyHistory.objects.all()
    team = TeamMember.objects.filter(is_active=True)
    values = CompanyValue.objects.all()

    context = {
        'histories': histories,
        'team': team,
        'values': values,
    }
    return render(request, 'about/index.html', context)

"""Views для contacts приложения."""

from django.shortcuts import render
from .models import Contact


def contacts_index(request):
    """Страница контактов."""

    try:
        contacts = Contact.objects.first()
    except Contact.DoesNotExist:
        contacts = None

    context = {
        'contacts': contacts,
    }
    return render(request, 'contacts/index.html', context)

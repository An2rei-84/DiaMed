"""Views для core приложения."""

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm as ContactFormForm


def index(request):
    """Главная страница."""
    # Получаем последние услуги для превью
    from apps.services.models import Service

    services = Service.objects.filter(is_active=True)[:6]

    # Контактная информация
    from apps.contacts.models import Contact
    try:
        contacts = Contact.objects.first()
    except Contact.DoesNotExist:
        contacts = None

    context = {
        'services': services,
        'contacts': contacts,
    }
    return render(request, 'core/index.html', context)


def contact_form_submit(request):
    """Обработка формы обратной связи."""
    if request.method == 'POST':
        form = ContactFormForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Ваше сообщение отправлено! Мы свяжемся с вами в ближайшее время.'
            )
            return redirect('core:index')
    else:
        form = ContactFormForm()

    return redirect('core:index')

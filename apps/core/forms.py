"""Forms для core приложения."""

from django import forms
from .models import ContactForm


class ContactForm(forms.ModelForm):
    """Форма обратной связи."""

    class Meta:
        """Настройки формы."""

        model = ContactForm
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Ваше сообщение...'
            }),
        }

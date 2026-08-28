"""Forms для users приложения."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Appointment, UserProfile


class UserRegisterForm(UserCreationForm):
    """Форма регистрации."""

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "email@example.com"})
    )
    first_name = forms.CharField(
        max_length=30, required=True, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя"})
    )
    last_name = forms.CharField(
        max_length=30, required=True, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Фамилия"})
    )

    class Meta:
        """Настройки формы."""

        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя пользователя"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Подтвердите пароль"}),
        }

    def save(self, commit=True):
        """Сохранение пользователя."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    """Форма входа."""

    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя пользователя"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Пароль"}))


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля."""

    class Meta:
        """Настройки формы."""

        model = UserProfile
        fields = ["phone", "date_of_birth", "address"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+7 (999) 123-45-67"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Ваш адрес"}),
        }


class AppointmentForm(forms.ModelForm):
    """Форма создания записи на приём."""

    def __init__(self, *args, **kwargs):
        """Инициализация с фильтром активных услуг."""
        super().__init__(*args, **kwargs)
        from apps.services.models import Service

        self.fields["service"].queryset = Service.objects.filter(is_active=True)
        # Устанавливаем минимальную дату - сегодня
        from datetime import date

        self.fields["date"].widget.attrs.update({"min": date.today().isoformat()})

    def clean_date(self):
        """Проверка что дата не в прошлом."""
        from datetime import date

        appointment_date = self.cleaned_data.get("date")
        if appointment_date and appointment_date < date.today():
            raise forms.ValidationError("Нельзя записаться на прошедшую дату.")
        return appointment_date

    class Meta:
        """Настройки формы."""

        model = Appointment
        fields = ["service", "date", "time", "notes"]
        widgets = {
            "service": forms.Select(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Дополнительные пожелания"}),
        }

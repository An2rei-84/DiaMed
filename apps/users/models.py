"""Модели users приложения."""

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Профиль пользователя."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile", verbose_name="Пользователь")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    address = models.TextField(blank=True, verbose_name="Адрес")

    class Meta:
        """Настройки модели."""

        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        """Строковое представление."""
        return f"Профиль: {self.user.get_full_name() or self.user.username}"


class Appointment(models.Model):
    """Запись на приём."""

    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("confirmed", "Подтверждена"),
        ("completed", "Завершена"),
        ("cancelled", "Отменена"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments", verbose_name="Пользователь")
    service = models.ForeignKey("services.Service", on_delete=models.CASCADE, verbose_name="Услуга")
    date = models.DateField(verbose_name="Дата")
    time = models.TimeField(verbose_name="Время")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    notes = models.TextField(blank=True, verbose_name="Примечания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    class Meta:
        """Настройки модели."""

        verbose_name = "Запись на приём"
        verbose_name_plural = "Записи на приём"
        ordering = ["-date", "-time"]

    def __str__(self):
        """Строковое представление."""
        return f"{self.user.get_full_name()} - {self.service.name} ({self.date})"


class DiagnosticResult(models.Model):
    """Результат диагностики."""

    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name="result", verbose_name="Запись на приём"
    )
    conclusion = models.TextField(verbose_name="Заключение")
    recommendations = models.TextField(blank=True, verbose_name="Рекомендации")
    doctor = models.CharField(max_length=100, verbose_name="Врач")
    result_date = models.DateField(auto_now_add=True, verbose_name="Дата результата")
    attachment = models.FileField(upload_to="results/%Y/%m/", blank=True, null=True, verbose_name="Файл результата (PDF)")
    is_normal = models.BooleanField(default=True, verbose_name="В норме", help_text="Поставьте галочку, если показатели в норме")

    class Meta:
        """Настройки модели."""

        verbose_name = "Результат диагностики"
        verbose_name_plural = "Результаты диагностики"
        ordering = ["-result_date"]

    def __str__(self):
        """Строковое представление."""
        return f"Результат: {self.appointment.service.name}"

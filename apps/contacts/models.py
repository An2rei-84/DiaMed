"""Модели contacts приложения."""

from django.db import models


class Contact(models.Model):
    """Контактная информация компании."""

    class Meta:
        """Настройки модели."""

        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"

    address = models.TextField(verbose_name="Адрес")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Email")
    working_hours = models.TextField(verbose_name="Время работы", help_text="Формат: Пн-Пт: 8:00-20:00")
    map_url = models.URLField(blank=True, verbose_name="Ссылка на карту")
    map_embed = models.TextField(blank=True, verbose_name="Код внедрения карты")

    def __str__(self):
        """Строковое представление."""
        return f"{self.address} - {self.phone}"

    def save(self, *args, **kwargs):
        """Сохранение с проверкой единственного экземпляра."""
        if not self.pk and Contact.objects.exists():
            raise ValueError("Может быть только один экземпляр Contact")
        return super().save(*args, **kwargs)

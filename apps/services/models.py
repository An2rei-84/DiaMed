"""Модели services приложения."""

from django.db import models


class ServiceCategory(models.Model):
    """Категория медицинских услуг."""

    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="URL")
    description = models.TextField(blank=True, verbose_name="Описание")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Иконка")

    class Meta:
        """Настройки модели."""

        verbose_name = "Категория услуг"
        verbose_name_plural = "Категории услуг"
        ordering = ["name"]

    def __str__(self):
        """Строковое представление."""
        return self.name


class Service(models.Model):
    """Медицинская услуга."""

    name = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="URL")
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="services", verbose_name="Категория")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена (₽)")
    duration = models.IntegerField(
        blank=True, null=True, verbose_name="Длительность (минут)", help_text="Оставьте пустым, если не применимо"
    )
    preparation = models.TextField(blank=True, verbose_name="Подготовка")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    image = models.ImageField(upload_to="services/", blank=True, null=True, verbose_name="Изображение")

    class Meta:
        """Настройки модели."""

        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ["category", "name"]

    def __str__(self):
        """Строковое представление."""
        return f"{self.name} - {self.price:.2f} ₽"

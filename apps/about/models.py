"""Модели about приложения."""

from django.db import models


class CompanyHistory(models.Model):
    """История компании."""

    year = models.IntegerField(verbose_name='Год')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    image = models.ImageField(
        upload_to='about/history/',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )

    class Meta:
        """Настройки модели."""

        verbose_name = 'Событие истории'
        verbose_name_plural = 'История компании'
        ordering = ['year']

    def __str__(self):
        """Строковое представление."""
        return f'{self.year} - {self.title}'


class TeamMember(models.Model):
    """Сотрудник компании."""

    name = models.CharField(max_length=100, verbose_name='ФИО')
    position = models.CharField(max_length=100, verbose_name='Должность')
    speciality = models.CharField(max_length=100, verbose_name='Специальность')
    experience = models.IntegerField(verbose_name='Стаж работы (лет)')
    photo = models.ImageField(
        upload_to='about/team/',
        blank=True,
        null=True,
        verbose_name='Фото'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        """Настройки модели."""

        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Команда'
        ordering = ['name']

    def __str__(self):
        """Строковое представление."""
        return f'{self.name} - {self.position}'


class CompanyValue(models.Model):
    """Ценности компании."""

    title = models.CharField(max_length=100, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Иконка (CSS класс)'
    )

    class Meta:
        """Настройки модели."""

        verbose_name = 'Ценность'
        verbose_name_plural = 'Ценности'
        ordering = ['id']

    def __str__(self):
        """Строковое представление."""
        return self.title

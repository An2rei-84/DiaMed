"""Модели core приложения."""

from django.db import models


class ContactForm(models.Model):
    """Сообщение из формы обратной связи."""

    name = models.CharField(max_length=100, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    message = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    is_processed = models.BooleanField(default=False, verbose_name='Обработано')

    class Meta:
        """Настройки модели."""

        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        """Строковое представление."""
        return f'{self.name} - {self.created_at.strftime("%d.%m.%Y")}'

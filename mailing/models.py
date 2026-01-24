from django.db import models


class MailingRecipient(models.Model):
    """Модель получателя рассылки"""

    email = models.EmailField(
        unique=True,
        max_length=100,
        verbose_name="Почта получателя",
        help_text="Введите почту получателя",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Имя получателя",
        help_text="Введите ФИО получателя",
    )
    comment = models.TextField(null=True, blank=True, verbose_name="Комментарий")


class Massage(models.Model):
    """Модель письма для рассылки"""

    letter_teme = models.CharField(max_length=100, verbose_name="Тема письма", help_text="Введите тему письма")
    letter_body = models.TextField(verbose_name="Содержание письма", help_text="Введите содержание письма")

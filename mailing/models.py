from django.db import models


class MailingRecipient(models.Model):
    email = models.EmailField(unique=True, max_length=100, verbose_name="Почта получателя", help_text="Введите почту получателя")
    name = models.CharField(max_length=100, verbose_name="Имя получателя",help_text="Введите ФИО получателя")
    comment = models.TextField(null=True, blank=True, verbose_name="Комментарий")

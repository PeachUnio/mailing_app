from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"


class Message(models.Model):
    """Модель письма для рассылки"""

    letter_theme = models.CharField(max_length=100, verbose_name="Тема письма", help_text="Введите тему письма")
    letter_body = models.TextField(verbose_name="Содержание письма", help_text="Введите содержание письма")

    class Meta:
        verbose_name = "Письмо"
        verbose_name_plural = "Письма"


class Mailing(models.Model):
    """Модель рассылки"""

    start_time = models.DateTimeField(verbose_name="Дата начала рассылки")
    end_time = models.DateTimeField(verbose_name="Дата конца рассылки")

    STATUS_CREATED = "created"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_COMPLETED, "Завершена"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name="Статус")

    massage = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name="Сообщение для рассылки")
    recipients = models.ManyToManyField(MailingRecipient, verbose_name="Получатели рассылки")

    @property
    def dynamic_status(self):
        """Динамически вычисляемый статус"""
        now = timezone.now()

        if now < self.start_time:
            return self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            return self.STATUS_RUNNING
        else:
            return self.STATUS_COMPLETED

    @property
    def status_display(self):
        """Отображаемое значение динамического статуса"""
        status_map = dict(self.STATUS_CHOICES)
        return status_map.get(self.dynamic_status, "Неизвестно")

    def update_status(self):
        """Обновляет статический статус в БД на основе динамического"""
        dynamic_status = self.dynamic_status

        if self.status != dynamic_status:
            self.status = dynamic_status
            self.save(update_fields=["status"])

    def clean(self):
        """Валидация для проверки дат"""
        if self.start_time >= self.end_time:
            raise ValidationError("Дата окончания должна быть позже даты начала")
        if self.start_time < timezone.now():
            raise ValidationError("Дата начала не может быть в прошлом")

    def save(self, *args, **kwargs):
        """Автоматический вызов clean при сохранении"""
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"


class MailingLog(models.Model):
    """Модель для хранения логов отправки"""
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        verbose_name="Рассылка",
        related_name='logs'
    )
    recipient = models.ForeignKey(
        MailingRecipient,
        on_delete=models.CASCADE,
        verbose_name="Получатель"
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время попытки"
    )

    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILED, 'Не успешно'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="Статус"
    )
    server_response = models.TextField(
        verbose_name="Ответ почтового сервера"
    )

    class Meta:
        verbose_name = "Лог рассылки"
        verbose_name_plural = "Логи рассылок"
        ordering = ['-attempt_time']

    def __str__(self):
        return f"Лог #{self.id} - {self.get_status_display()}"

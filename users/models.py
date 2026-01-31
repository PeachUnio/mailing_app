from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Почта не введена')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser должен быть сотрудником.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser должен быть разрешен доступ.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name='Email')

    token = models.CharField(max_length=32, blank=True, null=True, verbose_name='Токен')
    is_verified = models.BooleanField(default=False, verbose_name='Подтвержден')

    reset_token = models.CharField(max_length=32, blank=True, null=True, verbose_name='Токен сброса пароля')
    reset_token_expires = models.DateTimeField(blank=True, null=True, verbose_name='Срок действия токена сброса')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email
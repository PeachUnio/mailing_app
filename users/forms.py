from datetime import timedelta

from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import BooleanField, ModelForm
from django.utils import timezone

from users.models import User


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, BooleanField):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class UserRegisterForm(StyleFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "avatar", "phone", "country", "password1", "password2")

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Настройка виджетов для кастомных полей
            self.fields['avatar'].widget = forms.ClearableFileInput(attrs={
                'class': 'form-control'
            })
            self.fields['avatar'].required = False

            self.fields['phone'].widget = forms.TextInput(attrs={
                'class': 'form-control'
            })
            self.fields['phone'].required = False

            self.fields['country'].widget = forms.TextInput(attrs={
                'class': 'form-control'
            })
            self.fields['country'].required = False

            # Убедитесь, что email тоже правильно настроен
            self.fields['email'].widget = forms.EmailInput(attrs={
                'class': 'form-control',
                'autofocus': True
            })


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Введите ваш email"})
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email не найден")
        return email


class PasswordResetConfirmForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

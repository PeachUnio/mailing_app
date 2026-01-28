from django import forms
from .models import Mailing, Message, MailingRecipient


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'recipients']  # Исправлено: massage → message
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'message': forms.Select(attrs={'class': 'form-control'}),  # Исправлено
            'recipients': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
        labels = {
            'message': 'Сообщение для рассылки',  # Исправлено
            'recipients': 'Получатели',
        }
        help_texts = {
            'recipients': 'Удерживайте Ctrl (Cmd на Mac) для выбора нескольких получателей',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Опционально: загружаем все доступные сообщения
        self.fields['message'].queryset = Message.objects.all()
        # Загружаем всех получателей
        self.fields['recipients'].queryset = MailingRecipient.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(
                "Дата окончания должна быть позже даты начала"
            )

        return cleaned_data


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['letter_theme', 'letter_body']
        widgets = {
            'letter_theme': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Введите тему письма'}
            ),
            'letter_body': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Введите содержание письма'}
            ),
        }


class RecipientForm(forms.ModelForm):
    class Meta:
        model = MailingRecipient
        fields = ['email', 'name', 'comment']
        widgets = {
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': 'example@email.com'}
            ),
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Иван Иванов'}
            ),
            'comment': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Дополнительная информация'}
            ),
        }
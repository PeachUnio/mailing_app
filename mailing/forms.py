from django import forms

from .models import Mailing, MailingRecipient, Message


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "recipients"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "message": forms.Select(attrs={"class": "form-control"}),
            "recipients": forms.SelectMultiple(attrs={"class": "form-control"}),
        }
        labels = {
            "message": "Сообщение для рассылки",
            "recipients": "Получатели",
        }
        help_texts = {
            "recipients": "Удерживайте Ctrl (Cmd на Mac) для выбора нескольких получателей",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].queryset = Message.objects.all()
        self.fields["recipients"].queryset = MailingRecipient.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("Дата окончания должна быть позже даты начала")

        return cleaned_data


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["letter_theme", "letter_body"]
        widgets = {
            "letter_theme": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введите тему письма"}),
            "letter_body": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Введите содержание письма"}
            ),
        }


class RecipientForm(forms.ModelForm):
    class Meta:
        model = MailingRecipient
        fields = ["email", "name", "comment"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "example@email.com"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Иван Иванов"}),
            "comment": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Дополнительная информация"}
            ),
        }


class MailingModerForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["status"]

        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["status"].choices = [
            (Mailing.STATUS_RUNNING, "Запущена"),
            (Mailing.STATUS_DISABLED, "Отключена"),
        ]
        self.fields["status"].help_text = "Менеджер может только отключать рассылки"

    def clean_status(self):
        status = self.cleaned_data.get("status")
        return status
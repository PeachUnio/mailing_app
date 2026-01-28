from django.contrib import admin

from mailing.models import MailingRecipient, Message, Mailing


@admin.register(MailingRecipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "name")
    list_filter = ("name",)
    search_fields = ("name", "email")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "letter_theme")

@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "status")

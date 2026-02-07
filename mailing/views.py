from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView

from .forms import MailingForm, MessageForm, RecipientForm
from .models import Mailing, MailingLog, MailingRecipient, Message


class HomeView(TemplateView):
    template_name = "mailing/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        user = self.request.user

        if user.is_authenticated:
            is_manager = user.has_perm('mailing.can_view_all_mailings')

            if is_manager:
                mailings_qs = Mailing.objects.all()
                recipients_qs = MailingRecipient.objects.all()
            else:
                mailings_qs = Mailing.objects.filter(owner=user)
                recipients_qs = MailingRecipient.objects.filter(owner=user)

            context["total_mailings"] = mailings_qs.count()
            context["user_total_mailings"] = mailings_qs.count()

            context["active_mailings"] = mailings_qs.filter(
                start_time__lte=now,
                end_time__gte=now,
                status=Mailing.STATUS_RUNNING,
                is_active=True
            ).count()
            context["user_active_mailings"] = context["active_mailings"]

            context["unique_recipients"] = recipients_qs.distinct().count()
            context["user_recipients"] = recipients_qs.distinct().count()

            context["latest_mailings"] = mailings_qs.order_by("-start_time")[:5]

            if is_manager:
                context["recent_logs"] = MailingLog.objects.select_related(
                    "mailing", "recipient"
                ).order_by("-attempt_time")[:10]
            else:
                context["recent_logs"] = MailingLog.objects.filter(
                    mailing__in=mailings_qs
                ).select_related("mailing", "recipient").order_by("-attempt_time")[:10]

        else:
            context["total_mailings"] = 0
            context["active_mailings"] = 0
            context["unique_recipients"] = 0
            context["user_total_mailings"] = 0
            context["user_active_mailings"] = 0
            context["user_recipients"] = 0

        return context


class MailingListView(ListView):
    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        queryset = super().get_queryset()

        for mailing in queryset:
            mailing.update_status()
        return queryset


class MailingCreateView(CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_context_data(self, **kwargs):
        """Добавляем сообщения и получателей в контекст"""
        context = super().get_context_data(**kwargs)
        context["all_messages"] = Message.objects.all()
        context["all_recipients"] = MailingRecipient.objects.all()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Рассылка успешно создана!")
        mailing = form.save()
        user = self.request.user
        mailing.owner = user
        mailing.save()
        return super().form_valid(form)


class MailingUpdateView(UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_messages"] = Message.objects.all()
        context["all_recipients"] = MailingRecipient.objects.all()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Рассылка успешно обновлена!")
        return super().form_valid(form)


class MailingDeleteView(DeleteView):
    model = Mailing
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Рассылка успешно удалена!")
        return super().delete(request, *args, **kwargs)


class MailingDetailView(DetailView):
    model = Mailing
    template_name = "mailing/mailing_detail.html"
    context_object_name = "mailing"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mailing = self.object

        logs = mailing.logs.all()
        context["success_count"] = logs.filter(status="success").count()
        context["failed_count"] = logs.filter(status="failed").count()
        context["logs"] = logs.order_by("-attempt_time")[:20]

        return context


def send_mailing_now(request, pk):
    """Запуск рассылки вручную"""
    mailing = get_object_or_404(Mailing, pk=pk)

    if request.method == "POST":
        success, message = mailing.send_mailing()

        if success:
            messages.success(request, f"Рассылка запущена! {message}")
        else:
            messages.error(request, f"Ошибка: {message}")

        return redirect("mailing_detail", pk=pk)

    return redirect("mailing_detail", pk=pk)


class MessageListView(ListView):
    model = Message
    template_name = "mailing/message_list.html"


class MessageCreateView(CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        message = form.save()
        user = self.request.user
        message.owner = user
        message.save()
        return super().form_valid(form)


class MessageUpdateView(UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")


class RecipientListView(ListView):
    model = MailingRecipient
    template_name = "mailing/recipient_list.html"
    context_object_name = "recipients"


class RecipientCreateView(CreateView):
    model = MailingRecipient
    form_class = RecipientForm
    template_name = "mailing/recipient_form.html"
    success_url = reverse_lazy("mailing:recipient_list")

    def form_valid(self, form):
        recipient = form.save()
        user = self.request.user
        recipient.owner = user
        recipient.save()
        return super().form_valid(form)


class RecipientUpdateView(UpdateView):
    model = MailingRecipient
    form_class = RecipientForm
    template_name = "mailing/recipient_form.html"
    success_url = reverse_lazy("mailing:recipient_list")


class RecipientDeleteView(DeleteView):
    model = MailingRecipient
    template_name = "mailing/recipient_confirm_delete.html"
    success_url = reverse_lazy("mailing:recipient_list")

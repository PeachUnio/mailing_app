import secrets
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, FormView, View, ListView
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.core.mail import send_mail
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

from .forms import UserRegisterForm, PasswordResetRequestForm, PasswordResetConfirmForm
from .models import User
from config.settings import EMAIL_HOST_USER

class UserCreateView(CreateView):
    model = User
    template_name = "register_form.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token =token
        user.save()
        host = self.request.get_host()
        url = f"https://{host}/users/email-confirm/{token}/"
        send_mail(
            subject="подтверждение почты",
            message=f"добрый день! перейдите по ссылке для подтверждения почты\n{url}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email]
        )
        return super().form_valid(form)


def email_verification(request, token):
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.save()
    return redirect(reverse("users:login"))


class PasswordResetRequestView(FormView):
    template_name = 'password_reset_request.html'
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = User.objects.get(email=email)

        token = secrets.token_hex(16)
        user.reset_token = token
        user.reset_token_expires = timezone.now() + timedelta(hours=24)
        user.save()

        host = self.request.get_host()
        reset_url = f"https://{host}/users/password-reset-confirm/{token}/"

        send_mail(
            subject="Восстановление пароля",
            message=f"Для восстановления пароля перейдите по ссылке:\n{reset_url}\n\nСсылка действительна 24 часа.",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email]
        )

        messages.success(self.request, 'Инструкции по восстановлению пароля отправлены на ваш email.')
        return super().form_valid(form)


class PasswordResetConfirmView(FormView):
    template_name = 'password_reset_confirm.html'
    form_class = PasswordResetConfirmForm
    success_url = reverse_lazy('users:login')

    def dispatch(self, request, *args, **kwargs):
        self.token = kwargs.get('token')
        self.user = get_object_or_404(User, reset_token=self.token)

        if (self.user.reset_token_expires and
                self.user.reset_token_expires < timezone.now()):
            messages.error(request, 'Срок действия ссылки истек.')
            return redirect('users:password-reset')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        user = form.save()

        user.reset_token = None
        user.reset_token_expires = None
        user.save()

        messages.success(self.request, 'Пароль успешно изменен. Теперь вы можете войти с новым паролем.')
        return super().form_valid(form)

class UserListView(PermissionRequiredMixin, ListView):
    model = User
    template_name = "user_list.html"
    permission_required = 'mailing.can_view_all_mailings'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.filter(is_superuser=False).order_by('-date_joined')


class ToggleUserActiveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'mailing.can_disable_mailing'

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        if user == request.user:
            messages.error(request, "Вы не можете заблокировать себя")
            return redirect('users:user_list')

        user.is_active = not user.is_active
        user.save()

        action = "заблокирован" if not user.is_active else "разблокирован"
        messages.success(request, f"Пользователь {user.email} {action}")

        return redirect('users:user_list')

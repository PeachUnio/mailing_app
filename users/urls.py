from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from users.apps import UsersConfig
from users.views import UserCreateView, email_verification, PasswordResetRequestView, PasswordResetConfirmView, UserListView, ToggleUserActiveView

app_name = UsersConfig.name

urlpatterns = [
    path("login/", LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", UserCreateView.as_view(), name="register"),
    path("email-confirm/<str:token>/", email_verification, name="email-confirm"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset-confirm/<str:token>/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("list/", UserListView.as_view(), name="user_list"),
    path("toggle-active/<int:pk>/", ToggleUserActiveView.as_view(), name="toggle_user_active"),
]
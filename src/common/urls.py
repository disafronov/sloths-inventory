from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.views.i18n import set_language

from .views import EmailChangeConfirmView, ProfileView

app_name = "common"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("profile/", ProfileView.as_view(), name="profile"),
    path(
        "email/change/confirm/<uidb64>/<token>/<new_email>/",
        EmailChangeConfirmView.as_view(),
        name="email_change_confirm",
    ),
    # Password change now handled via ProfileView; separate URL removed.
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("i18n/setlang/", set_language, name="set_language"),
    # Password reset flow
    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name="password_reset_form.html",
            email_template_name="emails/password_reset_body.txt",
            html_email_template_name="emails/password_reset_body.html",
            subject_template_name="emails/password_reset_subject.txt",
            success_url=reverse_lazy("common:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html",
            success_url=reverse_lazy("common:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]

from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


class UserPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    """
    Password change page for non-staff users.

    The menu entry is shown only to non-staff users, but the endpoint itself does
    not block staff users to avoid surprising 403s for administrators.
    """

    template_name = "password_change.html"
    success_url = reverse_lazy("inventory:my-items")
    login_url = reverse_lazy("common:login")

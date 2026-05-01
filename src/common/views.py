from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


class UserPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    """
    Password change page for authenticated users (same entry as in the main nav).

    Staff may use Django Admin for account tasks as well; this view remains open to
    them so they are not surprised by a 403 when following the app-wide nav link.
    """

    template_name = "password_change.html"
    success_url = reverse_lazy("inventory:my-items")
    login_url = reverse_lazy("common:login")

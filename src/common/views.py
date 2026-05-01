from django.contrib.auth import views as auth_views
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponseBase
from django.urls import reverse_lazy


class UserPasswordChangeView(auth_views.PasswordChangeView):
    """
    Password change page for non-staff users.

    Staff users are expected to manage credentials in Django admin.
    """

    template_name = "password_change.html"
    success_url = reverse_lazy("inventory:my-items")

    def dispatch(
        self, request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponseBase:
        if request.user.is_authenticated and request.user.is_staff:
            raise PermissionDenied(
                "Staff users should change password in Django admin."
            )
        return super().dispatch(request, *args, **kwargs)

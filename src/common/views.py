from typing import TYPE_CHECKING, Any, cast

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    get_user_model,
    update_session_auth_hash,
)

# import removed – UserPasswordChangeView no longer used
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from common.email_tokens import email_change_token_generator
from common.email_utils import (
    send_email_change_confirmation,
    send_email_changed_notification,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import User as UserType

from .forms import EmailChangeForm

User = get_user_model()


# UserPasswordChangeView removed – password change handled via ProfileView.


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    User profile page with email and password change forms.
    """

    template_name = "profile.html"
    login_url = reverse_lazy("common:login")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = cast("UserType", self.request.user)
        context["email_form"] = EmailChangeForm(user=user)
        context["password_form"] = PasswordChangeForm(user=user)
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # Determine which form was submitted
        if "email_submit" in request.POST:
            return self._handle_email_change(request)
        elif "password_submit" in request.POST:
            return self._handle_password_change(request)
        return self.get(request, *args, **kwargs)

    def _handle_email_change(self, request: HttpRequest) -> HttpResponse:
        """Handle email change form submission."""
        user = cast("UserType", request.user)
        email_form = EmailChangeForm(user=user, data=request.POST)
        password_form = PasswordChangeForm(user=user)

        if email_form.is_valid():
            new_email = email_form.cleaned_data["new_email"]
            send_email_change_confirmation(user, new_email)
            if settings.EMAIL_SEND_ASYNC:
                msg = _(
                    "A confirmation email has been queued for delivery to "
                    "%(email)s. Please check your email to confirm the change."
                ) % {"email": new_email}
            else:
                msg = _(
                    "A confirmation email has been sent to %(email)s. "
                    "Please check your email to confirm the change."
                ) % {"email": new_email}
            messages.success(request, msg)
            return redirect("common:profile")
        # Render form with errors
        return render(
            request,
            "profile.html",
            {"email_form": email_form, "password_form": password_form},
        )

    def _handle_password_change(self, request: HttpRequest) -> HttpResponse:
        """Handle password change form submission."""
        user = cast("UserType", request.user)
        email_form = EmailChangeForm(user=user)
        password_form = PasswordChangeForm(user=user, data=request.POST)

        if password_form.is_valid():
            user = password_form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, _("Your password has been changed successfully."))
            return redirect("common:profile")
        # Render form with errors
        return render(
            request,
            "profile.html",
            {"email_form": email_form, "password_form": password_form},
        )


class EmailChangeConfirmView(View):
    """Confirm email change via token link."""

    def get(
        self,
        request: HttpRequest,
        uidb64: str,
        token: str,
        new_email: str,
    ) -> HttpResponse:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            new_email_decoded = force_str(urlsafe_base64_decode(new_email))
        except TypeError, ValueError, OverflowError, User.DoesNotExist:
            user = None
            new_email_decoded = None

        if user is not None and new_email_decoded is not None:
            if email_change_token_generator.check_token_for_email(
                user, token, new_email_decoded
            ):
                # Check if email is still available
                if (
                    User.objects.filter(email__iexact=new_email_decoded)
                    .exclude(pk=user.pk)
                    .exists()
                ):
                    messages.error(
                        request,
                        _("This email address is already in use by another account."),
                    )
                else:
                    # Update email
                    old_email = user.email
                    user.email = new_email_decoded
                    user.save(update_fields=["email"])
                    messages.success(
                        request,
                        _("Your email address has been changed successfully."),
                    )

                    send_email_changed_notification(user, old_email, new_email_decoded)

                return redirect("common:profile")

        messages.error(
            request,
            _(
                "The email confirmation link is invalid or has expired. "
                "Please request a new email change."
            ),
        )
        return redirect("common:profile")

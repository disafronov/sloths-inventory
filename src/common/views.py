from typing import TYPE_CHECKING, Any, cast

from django.contrib import messages
from django.contrib.auth import (
    get_user_model,
    update_session_auth_hash,
)
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

if TYPE_CHECKING:
    from django.contrib.auth.models import User as UserType

from .email_tokens import email_change_token_generator
from .forms import EmailChangeForm

User = get_user_model()


class UserPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    """
    Password change page for authenticated users (same entry as in the main nav).

    Staff may use Django Admin for account tasks as well; this view remains open to
    them so they are not surprised by a 403 when following the app-wide nav link.
    """

    template_name = "password_change.html"
    success_url = reverse_lazy("inventory:my-items")
    login_url = reverse_lazy("common:login")


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
            self._send_email_confirmation(user, new_email)
            messages.success(
                request,
                _(
                    "A confirmation email has been sent to %(email)s. "
                    "Please check your inbox and click the link to confirm the change."
                )
                % {"email": new_email},
            )
            return redirect("common:profile")

        return render(
            request,
            self.template_name,
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

        return render(
            request,
            self.template_name,
            {"email_form": email_form, "password_form": password_form},
        )

    def _send_email_confirmation(self, user: "UserType", new_email: str) -> None:
        """Send confirmation email to the new email address."""
        # Store new email temporarily for token generation
        user._new_email_for_token = new_email  # type: ignore[attr-defined]
        token = email_change_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build confirmation URL
        from django.conf import settings

        kwargs = {
            "uidb64": uid,
            "token": token,
            "new_email": urlsafe_base64_encode(force_bytes(new_email)),
        }
        path = reverse("common:email_change_confirm", kwargs=kwargs)
        confirmation_url = f"{settings.SITE_URL}{path}"

        # Send email
        subject = render_to_string(
            "emails/email_change_subject.txt", {"user": user}
        ).strip()
        text_body = render_to_string(
            "emails/email_change_body.txt",
            {
                "user": user,
                "new_email": new_email,
                "confirmation_url": confirmation_url,
            },
        )
        html_body = render_to_string(
            "emails/email_change_body.html",
            {
                "user": user,
                "new_email": new_email,
                "confirmation_url": confirmation_url,
            },
        )

        send_mail(
            subject=subject,
            message=text_body,
            from_email=None,  # Use DEFAULT_FROM_EMAIL
            recipient_list=[new_email],
            html_message=html_body,
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
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            new_email_decoded = None

        if user is not None and new_email_decoded is not None:
            # Validate token
            user._new_email_for_token = new_email_decoded  # type: ignore[attr-defined]
            if email_change_token_generator.check_token(user, token):
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

                    # Send notification to old email
                    self._send_notification_to_old_email(
                        user, old_email, new_email_decoded
                    )

                return redirect("common:profile")

        messages.error(
            request,
            _(
                "The email confirmation link is invalid or has expired. "
                "Please request a new email change."
            ),
        )
        return redirect("common:profile")

    def _send_notification_to_old_email(
        self, user: "UserType", old_email: str, new_email: str
    ) -> None:
        """Notify the old email address about the change."""
        subject = render_to_string(
            "emails/email_changed_notification_subject.txt", {"user": user}
        ).strip()
        text_body = render_to_string(
            "emails/email_changed_notification_body.txt",
            {"user": user, "old_email": old_email, "new_email": new_email},
        )
        html_body = render_to_string(
            "emails/email_changed_notification_body.html",
            {"user": user, "old_email": old_email, "new_email": new_email},
        )

        send_mail(
            subject=subject,
            message=text_body,
            from_email=None,
            recipient_list=[old_email],
            html_message=html_body,
        )

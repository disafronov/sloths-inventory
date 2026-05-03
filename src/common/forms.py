from typing import TYPE_CHECKING, Any

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.contrib.auth.models import User as UserType

User = get_user_model()


class EmailChangeForm(forms.Form):
    """Form for changing user's email address."""

    new_email = forms.EmailField(
        label=_("New email address"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    new_email_confirm = forms.EmailField(
        label=_("Confirm new email address"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    def __init__(self, user: "UserType", *args: Any, **kwargs: Any) -> None:
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_email(self) -> str | None:
        new_email = self.cleaned_data.get("new_email")
        if new_email and new_email.lower() == self.user.email.lower():
            raise ValidationError(
                _("The new email address must be different from the current one.")
            )
        # Check if email is already taken by another user
        if (
            new_email
            and User.objects.filter(email__iexact=new_email)
            .exclude(pk=self.user.pk)
            .exists()
        ):
            raise ValidationError(_("This email address is already in use."))
        return new_email.lower() if new_email else new_email

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if cleaned_data is None:
            return {}
        new_email = cleaned_data.get("new_email")
        new_email_confirm = cleaned_data.get("new_email_confirm")

        if new_email and new_email_confirm and new_email != new_email_confirm:
            raise ValidationError(
                {"new_email_confirm": _("The two email addresses do not match.")}
            )

        return cleaned_data

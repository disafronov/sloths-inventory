"""User-facing views for catalog management (locations)."""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from .models import Location, Responsible


class _LocationForm(forms.Form):
    """Form to create or rename a personal location."""

    name = forms.CharField(
        max_length=255,
        strip=True,
        error_messages={"required": _("Location name is required.")},
    )


@login_required
def location_list(request: HttpRequest) -> HttpResponse:
    """List personal locations for the current user, with optional search."""

    responsible = Responsible.linked_profile_for_user(request.user)
    has_any = False
    locations: list[Location] = []

    if responsible is not None:
        all_locations = Location.objects.filter(responsible=responsible).order_by(
            "name"
        )
        has_any = all_locations.exists()

        query = request.GET.get("q", "").strip()
        if query:
            locations = list(all_locations.filter(name__icontains=query))
        else:
            locations = list(all_locations)
    else:
        query = ""

    return render(
        request,
        "catalogs/location_list.html",
        {
            "locations": locations,
            "responsible": responsible,
            "query": query,
            "show_search": has_any,
        },
    )


@login_required
def location_create(request: HttpRequest) -> HttpResponse:
    """Create a new personal location."""

    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        messages.error(
            request,
            _("Your account is not linked to a responsible person profile yet."),
        )
        return redirect("catalogs:location-list")

    if request.method == "POST":
        form = _LocationForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "catalogs/location_form.html",
                {
                    "error": str(form.errors.get("name", [""])[0]),
                    "name": form.data.get("name", ""),
                },
                status=400,
            )

        name = form.cleaned_data["name"]
        with transaction.atomic():
            Location.objects.create(name=name, responsible=responsible)
        messages.success(
            request,
            _("Location “%(name)s” has been created.") % {"name": name},
        )
        return redirect("catalogs:location-list")

    return render(request, "catalogs/location_form.html", {"name": ""})


@login_required
def location_edit(request: HttpRequest, *, location_id: int) -> HttpResponse:
    """Edit an existing personal location."""

    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        messages.error(
            request,
            _("Your account is not linked to a responsible person profile yet."),
        )
        return redirect("catalogs:location-list")

    location = get_object_or_404(Location, pk=location_id, responsible=responsible)

    if request.method == "POST":
        form = _LocationForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "catalogs/location_form.html",
                {
                    "location": location,
                    "error": str(form.errors.get("name", [""])[0]),
                    "name": location.display_name,
                },
                status=400,
            )

        old_name = location.display_name
        name = form.cleaned_data["name"]
        with transaction.atomic():
            location.name = name
            try:
                location.save()
            except ValidationError as exc:
                messages.error(request, exc.messages[0] if exc.messages else str(exc))
                return redirect("catalogs:location-edit", location_id=location_id)
        messages.success(
            request,
            _("Location “%(old_name)s” has been renamed to “%(name)s”.")
            % {"old_name": old_name, "name": name},
        )
        return redirect("catalogs:location-list")

    return render(
        request,
        "catalogs/location_form.html",
        {"location": location, "name": location.display_name},
    )


@login_required
def location_delete(request: HttpRequest, *, location_id: int) -> HttpResponse:
    """Delete a personal location that is not in use."""

    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        messages.error(
            request,
            _("Your account is not linked to a responsible person profile yet."),
        )
        return redirect("catalogs:location-list")

    location = get_object_or_404(Location, pk=location_id, responsible=responsible)

    if location.is_catalog_reference_in_use():
        messages.error(
            request,
            _(
                "Location “%(name)s” is in use by one or more items and "
                "cannot be deleted."
            )
            % {"name": location.display_name},
        )
        return redirect("catalogs:location-list")

    if request.method == "POST":
        name = location.display_name
        with transaction.atomic():
            location.delete()
        messages.success(
            request,
            _("Location “%(name)s” has been deleted.") % {"name": name},
        )
        return redirect("catalogs:location-list")

    return render(
        request,
        "catalogs/location_confirm_delete.html",
        {"location": location},
    )

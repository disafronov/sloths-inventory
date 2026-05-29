from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from common.admin import BaseAdmin, CatalogReferenceAdminMixin, NamedModelAdmin

from .models import Location, Responsible, Status


@admin.register(Location)
class LocationAdmin(NamedModelAdmin):
    list_display = [
        "location_display_name",
        "responsible_display",
        "updated_at",
        "created_at",
    ]
    list_display_links = ["location_display_name"]
    list_filter = ["responsible", "updated_at", "created_at"]
    search_fields = [
        "name",
        "responsible__last_name",
        "responsible__first_name",
        "responsible__middle_name",
        "created_at",
        "updated_at",
        "notes",
    ]
    autocomplete_fields = ["responsible"]
    main_fields = ("name", "responsible")

    @admin.display(description=_("Location"), ordering="name")
    def location_display_name(self, obj: Location) -> str:
        return obj.display_name

    @admin.display(description=_("Responsible"), ordering="responsible")
    def responsible_display(self, obj: Location) -> str:
        if obj.responsible_id is None:
            return _("Global: %(key)s") % {"key": obj.name}
        return str(obj.responsible)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Location]:
        qs = super().get_queryset(request)
        return qs.select_related("responsible")


@admin.register(Responsible)
class ResponsibleAdmin(CatalogReferenceAdminMixin, BaseAdmin):
    list_display = [
        "last_name",
        "first_name",
        "middle_name",
        "employee_id",
        "user",
        "updated_at",
        "created_at",
    ]
    list_display_links = [
        "last_name",
        "first_name",
        "middle_name",
        "employee_id",
        "user",
    ]
    list_filter = ["last_name", "first_name", "user", "updated_at", "created_at"]
    search_fields = [
        "last_name",
        "first_name",
        "middle_name",
        "employee_id",
        "user__username",
        "user__email",
    ]
    autocomplete_fields = ["user"]
    main_fields = (
        "last_name",
        "first_name",
        "middle_name",
        "employee_id",
        "user",
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Responsible]:
        """
        Avoid N+1 queries in admin list pages by preloading the related user.
        """

        qs = super().get_queryset(request)
        return qs.select_related("user")


@admin.register(Status)
class StatusAdmin(NamedModelAdmin):
    pass

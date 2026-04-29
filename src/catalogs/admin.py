from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from common.admin import BaseAdmin, NamedModelAdmin

from .models import Location, Responsible, Status


@admin.register(Location)
class LocationAdmin(NamedModelAdmin):
    pass


@admin.register(Responsible)
class ResponsibleAdmin(BaseAdmin):
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

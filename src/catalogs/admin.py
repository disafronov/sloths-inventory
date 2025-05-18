from django.contrib import admin
from .models import Location, Responsible, Status


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Responsible)
class ResponsibleAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "middle_name", "employee_id"]
    list_filter = ["last_name", "first_name"]
    search_fields = ["last_name", "first_name", "middle_name", "employee_id"]
    ordering = ["last_name", "first_name", "middle_name"]


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]

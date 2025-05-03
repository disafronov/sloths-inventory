from django.contrib import admin
from .models import Vendor, Model, Device

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "updated_at", "created_at")
    list_display_links = ("name", "description")
    search_fields = ("name", "description")
    list_filter = ("updated_at", "created_at")

@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "updated_at", "created_at")
    list_display_links = ("name", "description")
    search_fields = ("name", "description")
    list_filter = ("updated_at", "created_at")

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("vendor", "model", "serial_number", "description", "updated_at", "created_at")
    list_display_links = ("vendor", "model", "serial_number", "description")
    search_fields = ("serial_number", "description")
    list_filter = ("vendor", "model", "updated_at", "created_at")

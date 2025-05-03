from django.contrib import admin
from .models import Vendor, Model, Device

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("created_at", "updated_at")

@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("created_at", "updated_at")

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("vendor", "model", "serial_number", "created_at", "updated_at")
    search_fields = ("serial_number", "description")
    list_filter = ("vendor", "model", "created_at", "updated_at")

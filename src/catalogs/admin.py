from django.contrib import admin
from .models import Category, Vendor, Model, Device

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "updated_at", "created_at")
    list_display_links = ("name", "description")
    search_fields = ("name", "description")
    list_filter = ("updated_at", "created_at")

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
    list_display = ("category", "vendor", "model", "catalog_number", "description", "updated_at", "created_at")
    list_display_links = ("category", "vendor", "model", "catalog_number", "description")
    search_fields = ("catalog_number", "description")
    list_filter = ("category", "vendor", "model", "updated_at", "created_at")

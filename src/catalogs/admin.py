from django.contrib import admin
from .models import Category, Manufacturer, Model, Device

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "updated_at", "created_at")
    list_display_links = ("name", "description")
    search_fields = ("name", "description")
    list_filter = ("updated_at", "created_at")

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
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
    list_display = ("catalog_number", "category", "manufacturer", "model", "description", "updated_at", "created_at")
    list_display_links = ("catalog_number", "category", "manufacturer", "model", "description")
    search_fields = ("catalog_number", "description")
    list_filter = ("category", "manufacturer", "model", "updated_at", "created_at")

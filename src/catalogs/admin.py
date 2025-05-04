from django.contrib import admin
from .models import Category, Manufacturer, Model, Type, Device

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

@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "updated_at", "created_at")
    list_display_links = ("name", "description")
    search_fields = ("name", "description")
    list_filter = ("updated_at", "created_at")

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("category", "type", "manufacturer", "model", "description", "updated_at", "created_at")
    list_display_links = ("category", "type", "manufacturer", "model", "description")
    search_fields = (
        "description",
        "category__name",
        "type__name",
        "manufacturer__name",
        "model__name"
    )
    list_filter = ("category", "type", "manufacturer", "model", "updated_at", "created_at")
    autocomplete_fields = ["category", "type", "manufacturer", "model"]

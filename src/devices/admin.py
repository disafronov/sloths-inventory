from django.contrib import admin
from .models import Device
from .attributes import Category, Manufacturer, Model, Type


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["category", "type", "manufacturer", "model"]
    list_filter = ["category", "type", "manufacturer"]
    search_fields = ["category__name", "type__name", "manufacturer__name", "model__name"]
    ordering = ["category", "type", "manufacturer", "model"]

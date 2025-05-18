from django.contrib import admin
from common.admin import BaseAdmin, NamedModelAdmin
from .models import Device
from .attributes import Category, Manufacturer, Model, Type


@admin.register(Category)
class CategoryAdmin(NamedModelAdmin):
    pass


@admin.register(Manufacturer)
class ManufacturerAdmin(NamedModelAdmin):
    pass


@admin.register(Model)
class ModelAdmin(NamedModelAdmin):
    pass


@admin.register(Type)
class TypeAdmin(NamedModelAdmin):
    pass


@admin.register(Device)
class DeviceAdmin(BaseAdmin):
    list_display = ["category", "type", "manufacturer", "model", "updated_at", "created_at"]
    list_display_links = ["category", "type", "manufacturer", "model"]
    list_filter = ["category", "type", "manufacturer"]
    search_fields = ["category__name", "type__name", "manufacturer__name", "model__name", "notes", "created_at", "updated_at"]
    ordering = ["category", "type", "manufacturer", "model"]
    main_fields = ("category", "type", "manufacturer", "model")

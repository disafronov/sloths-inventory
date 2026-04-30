from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from common.admin import BaseAdmin, NamedModelAdmin

from .attributes import Category, Manufacturer, Model, Type
from .models import Device


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
    list_display = [
        "category",
        "type",
        "manufacturer",
        "model",
        "updated_at",
        "created_at",
    ]
    list_display_links = ["category", "type", "manufacturer", "model"]
    list_filter = ["category", "type", "manufacturer"]
    search_fields = [
        "category__name",
        "type__name",
        "manufacturer__name",
        "model__name",
        "notes",
        "created_at",
        "updated_at",
    ]
    ordering = ["category", "type", "manufacturer", "model"]
    main_fields = ("category", "type", "manufacturer", "model")
    autocomplete_fields = ["category", "type", "manufacturer", "model"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Device]:
        """
        Avoid N+1 queries in admin list pages by preloading FK relations.
        """

        qs = super().get_queryset(request)
        return qs.select_related("category", "type", "manufacturer", "model")

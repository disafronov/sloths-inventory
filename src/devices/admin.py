from django.contrib import admin
from .models import Category, Manufacturer, Model, Type


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at", "created_at")
    list_display_links = ("name",)
    search_fields = ("name",)
    list_filter = ("updated_at", "created_at")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = ((None, {"fields": ("name", "notes", "updated_at", "created_at")}),)


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at", "created_at")
    list_display_links = ("name",)
    search_fields = ("name",)
    list_filter = ("updated_at", "created_at")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = ((None, {"fields": ("name", "notes", "updated_at", "created_at")}),)


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at", "created_at")
    list_display_links = ("name",)
    search_fields = ("name",)
    list_filter = ("updated_at", "created_at")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = ((None, {"fields": ("name", "notes", "updated_at", "created_at")}),)


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at", "created_at")
    list_display_links = ("name",)
    search_fields = ("name",)
    list_filter = ("updated_at", "created_at")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = ((None, {"fields": ("name", "notes", "updated_at", "created_at")}),)

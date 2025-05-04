from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('inventory_number', 'device', 'serial_number', 'status', 'location', 'updated_at', 'created_at')
    list_display_links = ('inventory_number', 'device', 'serial_number')
    list_filter = ('status', 'device__category', 'device__type', 'device__manufacturer', 'updated_at', 'created_at')
    search_fields = (
        'inventory_number',
        'serial_number',
        'location',
        'notes',
        'device__category__name',
        'device__type__name',
        'device__manufacturer__name',
        'device__model__name',
        'device__description'
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['device']
    ordering = ['inventory_number']
    fieldsets = (
        (None, {
            'fields': ('inventory_number', 'device', 'serial_number', 'status', 'updated_at', 'created_at')
        }),
        ('Дополнительная информация', {
            'fields': ('location', 'notes'),
            'classes': ('collapse',)
        })
    )

from django.contrib import admin
from .models import Item, Operation

@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('item', 'status', 'responsible', 'location', 'updated_at', 'created_at')
    list_display_links = ('item', 'status', 'location')
    list_filter = ('status', 'responsible', 'item__device__category', 'item__device__type', 'item__device__manufacturer', 'updated_at', 'created_at')
    search_fields = (
        'item__inventory_number',
        'item__serial_number',
        'location',
        'notes',
        'responsible__username',
        'responsible__first_name',
        'responsible__last_name',
        'item__device__category__name',
        'item__device__type__name',
        'item__device__manufacturer__name',
        'item__device__model__name',
        'item__device__description'
    )
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ['item']
    autocomplete_fields = ['responsible']
    ordering = ['-created_at']
    fieldsets = (
        (None, {
            'fields': ('item', 'status', 'responsible', 'location', 'notes', 'updated_at', 'created_at')
        }),
    )

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('inventory_number', 'device', 'serial_number', 'current_status', 'current_responsible', 'current_location', 'updated_at', 'created_at')
    list_display_links = ('inventory_number', 'device', 'serial_number')
    list_filter = ('device__category', 'device__type', 'device__manufacturer', 'updated_at', 'created_at')
    search_fields = (
        'inventory_number',
        'serial_number',
        'notes',
        'device__category__name',
        'device__type__name',
        'device__manufacturer__name',
        'device__model__name',
        'device__description'
    )
    readonly_fields = ('created_at', 'updated_at', 'current_status', 'current_location', 'current_responsible')
    autocomplete_fields = ['device']
    ordering = ['inventory_number']
    fieldsets = (
        (None, {
            'fields': ('inventory_number', 'device', 'serial_number', 'notes', 'updated_at', 'created_at')
        }),
        ('Текущая эксплуатация', {
            'fields': ('current_status', 'current_responsible', 'current_location'),
            'classes': ('collapse',)
        }),
    )

    def current_status(self, obj):
        return obj.status
    current_status.short_description = 'Статус'

    def current_location(self, obj):
        return obj.location
    current_location.short_description = 'Местоположение'

    def current_responsible(self, obj):
        return obj.responsible
    current_responsible.short_description = 'Ответственный'

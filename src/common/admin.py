from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ["created_at", "updated_at"]
    list_display = ["updated_at", "created_at"]
    search_fields = ["created_at", "updated_at", "notes"]
    fieldsets = (
        (None, {
            "fields": ()  # Будет переопределено в дочерних классах
        }),
        ("Дополнительная информация", {
            "fields": ("notes", "updated_at", "created_at")
        }),
    )
    main_fields = ()  # Будет переопределено в дочерних классах

    def get_main_fields(self):
        return self.main_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        fieldsets[0] = (None, {"fields": self.get_main_fields()})
        return fieldsets


class NamedModelAdmin(BaseAdmin):
    list_display = ["name", "updated_at", "created_at"]
    search_fields = ["name", "created_at", "updated_at", "notes"]
    main_fields = ("name",)

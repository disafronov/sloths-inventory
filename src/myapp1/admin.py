from django.contrib import admin

from myapp1.models import Department, Worker


class DepartmentAdmin(admin.ModelAdmin):
    def get_fields_custom():
        # return [field.name for field in Department._meta.get_fields()]
        return ["title", "phone"]

    list_display = get_fields_custom()
    search_fields = get_fields_custom()
    list_filter = get_fields_custom()


admin.site.register(Department, DepartmentAdmin)


class WorkerAdmin(admin.ModelAdmin):
    def get_fields_custom():
        # return [field.name for field in Worker._meta.get_fields()]
        return ["name", "second_name", "salary", "department"]

    list_display = get_fields_custom()
    search_fields = get_fields_custom()
    list_filter = get_fields_custom()


admin.site.register(Worker, WorkerAdmin)

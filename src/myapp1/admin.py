from django.contrib import admin

from myapp1.models import Worker

# Register your models here.
class WorkerAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Worker._meta.get_fields()]

admin.site.register(Worker, WorkerAdmin)

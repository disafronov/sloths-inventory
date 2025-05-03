from django.contrib import admin
from .models import Vendor, Model, Device

admin.site.register(Vendor)
admin.site.register(Model)
admin.site.register(Device)

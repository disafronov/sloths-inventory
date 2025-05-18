from django.apps import AppConfig
import os


class DevicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "devices"
    verbose_name = "Устройства"
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "devices")

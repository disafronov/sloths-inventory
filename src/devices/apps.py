from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import os


class DevicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "devices"
    verbose_name = _("Devices")
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "devices")

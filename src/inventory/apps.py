from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import os


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"
    verbose_name = _("Inventory")
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inventory")

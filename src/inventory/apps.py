from django.apps import AppConfig
import os


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"
    verbose_name = "Инвентарь"
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inventory")

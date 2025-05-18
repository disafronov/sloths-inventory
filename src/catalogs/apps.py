from django.apps import AppConfig
import os


class CatalogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalogs"
    verbose_name = "Каталоги"
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "catalogs")

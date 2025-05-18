from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
import os


class CatalogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalogs"
    verbose_name = _("Catalogs")
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "catalogs")

from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self) -> None:
        from common.application_groups import (
            connect_application_group_signals,
            enforce_application_groups,
        )

        connect_application_group_signals()
        # Runs while ``django.apps.apps.ready`` is still false (before other apps'
        # ``ready()`` hooks finish). Django may emit a runtime warning here; that is
        # acceptable because we need groups in place for management commands and
        # tests as soon as the auth tables exist.
        try:
            enforce_application_groups()
        except (OperationalError, ProgrammingError):
            # Migrations not applied yet (or DB unavailable during startup checks).
            pass

from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Django application config for the common app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self) -> None:
        """Connect application group signals on startup."""
        from common.application_groups import connect_application_group_signals

        connect_application_group_signals()

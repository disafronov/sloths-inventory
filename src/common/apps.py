from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self) -> None:
        from common.application_groups import connect_application_group_signals

        connect_application_group_signals()

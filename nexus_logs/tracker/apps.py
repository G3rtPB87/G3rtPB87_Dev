from django.apps import AppConfig as DjangoAppConfig


class TrackerConfig(DjangoAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tracker"

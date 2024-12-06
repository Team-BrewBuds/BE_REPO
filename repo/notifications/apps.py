from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "repo.notifications"

    def ready(self):
        import repo.notifications.signals  # noqa

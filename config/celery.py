import os

from celery import Celery

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings._base')

if os.environ.get("DEBUG") == "True":
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
else:
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

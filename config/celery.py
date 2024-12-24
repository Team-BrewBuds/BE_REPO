import os

from celery import Celery
from celery.schedules import crontab

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings._base')

if os.environ.get("DEBUG") == "True":
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.dev"
else:
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "cache-top-posts": {  # 매주 월요일 00:00 인기 게시글 캐시 업데이트
        "task": "repo.records.posts.tasks.cache_top_posts",
        "schedule": crontab(hour=0, minute=0, day_of_week=1),
    },
}

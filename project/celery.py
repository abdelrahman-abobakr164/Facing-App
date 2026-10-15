from celery.schedules import crontab
from celery import Celery
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_media.settings")

app = Celery("social_media")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "delete-expired-stories-every-hour": {
        "task": "story.tasks.delete_expired_stories",
        "schedule": crontab(minute=0),
    },
}

from .models import Story
from celery import shared_task
from django.utils import timezone


@shared_task
def delete_expired_stories():
    deleted_count, _ = Story.objects.filter(expires_at__lt=timezone.now()).delete()
    return deleted_count

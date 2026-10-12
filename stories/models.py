from django.db import models, transaction
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.db.models import Q
from django.db import models
import uuid
from django.db.models.signals import post_delete

from accounts.models import Follow
from posts.models import BaseLike

User = settings.AUTH_USER_MODEL

STORY_LIFETIME = timedelta(hours=24)


def default_expiry():
    return timezone.now() + STORY_LIFETIME


class StoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(expires_at__gt=timezone.now())

    def visible_to(self, user):
        follow = Follow.objects.filter(
            following=user, status=Follow.Status.ACCEPTED
        ).values("follower_id")
        return self.active().filter(Q(author=user)| Q(author__in=follow))

class Story(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stories")
    media = models.FileField(upload_to="stories/%Y/%m/%d/")
    media_type = models.CharField(max_length=5, choices=MediaType.choices, null=True, blank=True)
    caption = models.CharField(max_length=200, blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)

    objects = StoryQuerySet.as_manager()

    class Meta:
        verbose_name_plural = "stories"
        indexes = [
            models.Index(fields=["author", "expires_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Story {self.pk} by {self.author_id}"

    @property
    def is_active(self):
        return not self.expires_at > timezone.now()


class StoryView(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="views")
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="viewers")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["story", "viewer"], name="unique_story_view"
            )
        ]
        indexes = [models.Index(fields=["story", "-viewed_at"])]


class StoryLike(BaseLike):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "story"], name="unique_story_like")
        ]
        indexes = [models.Index(fields=["story", "-created_at"])]


@receiver(post_delete, sender=Story)
def delete_story_file(sender, instance, **kwargs):
    """Remove the media file only after the DB transaction commits."""
    if instance.media:
        storage, name = instance.media.storage, instance.media.name
        transaction.on_commit(lambda: storage.delete(name))

from pathlib import Path
import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)ss")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Post(TimeStamped):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    caption = models.CharField(null=True, blank=True, max_length=2000)
    body = models.TextField(null=True, blank=True)
    like_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}"

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]


class Comment(TimeStamped):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    body = models.TextField()
    likes_count = models.PositiveIntegerField(default=0)
    replies_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["post", "parent", "-created_at"]),
            models.Index(fields=["parent", "created_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.parent_id and self.parent.parent_id:
            self.parent = self.parent.parent
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}"


class PostLike(BaseLike):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_post_like")
        ]
        indexes = [models.Index(fields=["post", "-created_at"])]


class CommentLike(BaseLike):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "comment"], name="unique_comment_like"
            )
        ]
        indexes = [models.Index(fields=["comment", "-created_at"])]


class PostMedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="media")
    file = models.ImageField(upload_to="posts/%Y/%m/")

    def media_type(self):
        if not self.file:
            return None
        ext = Path(self.file.name).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            return "image"
        if ext in VIDEO_EXTENSIONS:
            return "video"
        return None

    class Meta:
        ordering = ["id"]

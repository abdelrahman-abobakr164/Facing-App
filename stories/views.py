from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, F
from django.http import JsonResponse
import os

from .models import *
from posts.utils import *
from posts.decorator import owner_ship_required
from posts.validators import validation_image, validation_video

IMAGE_EXTS = {"jpg", "jpeg", "png", "webp"}
VIDEO_EXTS = {"mp4", "mov", "webm"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024


@login_required
@require_POST
def like(request, id):
    next_url = get_safe_next_url(request)
    story = get_object_or_404(Story.objects.visible_to(request.user), id=id)

    if story.author.id != request.user.id:
        with transaction.atomic():
            _, created = StoryLike.objects.get_or_create(user=request.user, story=story)
            if created:
                Story.objects.filter(id=id).update(likes_count=F("likes_count") + 1)

        return redirect(next_url)


@login_required
def mark_seen(request, id):
    story = get_object_or_404(Story.objects.visible_to(request.user), id=id)
    if story.author.id != request.user.id:
        with transaction.atomic():
            _, created = StoryView.objects.get_or_create(
                viewer=request.user, story=story
            )
            if created:
                Story.objects.filter(id=id).update(views_count=F("views_count") + 1)


@login_required
def viewer(request, id):
    story = get_object_or_404(Story, id=id)
    mark_seen(request, id)
    is_liked = StoryLike.objects.filter(story=story, user=request.user).exists()

    return render(
        request, "stories/viewer.html", {"story": story, "is_liked": is_liked}
    )


@login_required
@owner_ship_required(Story, id_kwarg="id", user="author")
def viewers(request, id):
    story = get_object_or_404(Story, author=request.user, id=id)
    story_views = (
        StoryView.objects.filter(story_id=id)
        .select_related("viewer")
        .annotate(
            is_liked=Exists(
                StoryLike.objects.filter(story=story, user=OuterRef("viewer_id"))
            )
        )
        .order_by("-viewed_at")
    )
    context = {"story_views": story_views, "story": story}
    return render(request, "stories/viewers.html", context)


@login_required
@require_POST
def create(request):
    next_url = get_safe_next_url(request)
    caption = request.POST.get("caption")
    media = request.FILES.get("media")

    if not (caption or media):
        raise ValidationError("Write something or add a photo or a video.")

    if media:
        ext = os.path.splitext(media.name)[1].lower().lstrip(".")
        if ext in IMAGE_EXTS:
            validation_image(media)
            media_type = "image"
        elif ext in VIDEO_EXTS:
            validation_video(media)
            media_type = "video"
        else:
            raise ValidationError("Unsupported file type.")
    Story.objects.create(
        author=request.user,
        caption=caption,
        media=media,
        media_type=media_type if media else None,
    )

    return redirect(next_url)


@login_required
@owner_ship_required(Story, id_kwarg="id", user="author")
@require_POST
def delete(request, id):
    get_object_or_404(Story, author=request.user, id=id).delete()
    return redirect("/")

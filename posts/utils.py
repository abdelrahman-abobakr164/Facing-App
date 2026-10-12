from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from django.urls import reverse

from .models import Post, PostMedia
from .validators import validation_image, validation_video


def get_safe_next_url(request, default="home"):
    next_url = request.POST.get("next")
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse(default)


def validate_uploads(images, videos):
    errors = []
    checks = [(f, validation_image) for f in images] + [
        (f, validation_video) for f in videos
    ]

    for file, validator in checks:
        try:
            validator(file)
        except ValidationError as error:
            errors.extend(error.messages)

    if errors:
        raise ValidationError(errors)


def attach_media(post, images, videos):
    for file in (*images, *videos):
        PostMedia.objects.create(post=post, file=file)


def remove_media(post, media_id):
    media = get_object_or_404(PostMedia, id=media_id, post=post)
    media.delete()


def create_post(request):
    videos = request.FILES.getlist("video")
    images = request.FILES.getlist("image")
    content = request.POST.get("content", "").strip()

    if not (content or images or videos):
        raise ValidationError("Write something or add a photo or a video.")

    validate_uploads(images, videos)

    with transaction.atomic():
        post = Post.objects.create(
            user=request.user,
            body=content if not images or videos else content,
            caption=content,
        )

        attach_media(post, images, videos)


def post_update(request, post):
    images = request.FILES.getlist("add_image")
    videos = request.FILES.getlist("add_video")
    media_id = request.POST.get("remove_media")

    validate_uploads(images, videos)

    with transaction.atomic():
        if "content" in request.POST:
            post.body = request.POST["content"].strip()
        if "caption" in request.POST:
            post.caption = request.POST["caption"].strip()
        post.save()
        if media_id:
            remove_media(post, media_id)
        attach_media(post, images, videos)


@require_POST
@login_required
def post_commit(request, id=None):
    next_url = get_safe_next_url(request)
    post = get_object_or_404(Post, id=id, user=request.user) if id else None
    try:
        if post:
            post_update(request, post)
        else:
            create_post(request)
    except ValidationError as error:
        for message in error.messages:
            messages.error(request, message)

    return redirect(next_url)

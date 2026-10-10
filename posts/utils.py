from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect, get_object_or_404
from .models import Post, PostMedia
from django.db import transaction
from django.urls import reverse

IMAGE_EXTENSIONS = ["JPG", "jpg", "jpeg", "png", "PNG"]
VIDEO_EXTENSIONS = ["mp4", "mp3"]
FILE_SIZE = 1024 * 1024 * 10


def validate_file_size(file):
    return file.size <= FILE_SIZE


def image_validation(image):
    image_extension = image.name.split(".")[-1] if "." in image.name else ""
    return image_extension in IMAGE_EXTENSIONS


def video_validation(video):
    video_extension = video.name.split(".")[-1] if "." in video.name else ""
    return video_extension in VIDEO_EXTENSIONS


def video_adding(add_video, post):
    print(f"before for {add_video}")
    for video in add_video:
        print(f"after for {video}")
        if not video_validation(video):
            return redirect(next)
        add_post = PostMedia.objects.create(post=post, file=video)
    return add_post


def image_adding(add_image, post):
    print(f"before for {add_image}")
    for image in add_image:
        print(f"after for {image}")
        print(image)
        if not image_validation(image):
            return redirect(next)
        add_post = PostMedia.objects.create(post=post, file=image)
    return add_post


def post_commit(request, id):
    if request.method == "POST":
        next_url = request.POST.get("next")
        add_image = request.FILES.getlist("add_image")
        add_video = request.FILES.getlist("add_video")
        content = request.POST.get("content")
        caption = request.POST.get("caption")
        remove_media = request.POST.get("remove_media")

        if not url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            if request.path == "profile":
                next_url = reverse("profile", args=[id])
            else:
                next_url = reverse("home")

        post = get_object_or_404(Post, id=id)
        with transaction.atomic():
            if remove_media:
                print("Yes remove media")
                post.media.all().delete()
                if add_video:
                    video_adding(add_video, post)
                if add_image:
                    image_adding(add_image, post)
                return redirect(next_url)

            elif add_video:
                print("add_video")
                video_adding(add_video, post)

            elif add_image:
                print("in if add_image")
                image_adding(add_image, post)

            post.caption = caption
            post.save()

            if content:
                Post.objects.create(user=request.user, body=content)
            return redirect(next_url)
    return redirect("/")

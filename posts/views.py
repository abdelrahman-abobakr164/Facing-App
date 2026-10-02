from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from .decorator import owner_ship_required
from django.db import transaction
from django.db.models import F
from .models import *

# Create your views here.


def home(request):
    return render(request, "posts/home.html")


@owner_ship_required(Post, id_kwarg="id", user="user")
def delete_post(request, id):
    if request.method == "POST":
        get_object_or_404(Post, id=id).delete()
        return redirect(request.META.get("HTTP_REFERER"))
    return render(request, "posts/post-edit.html")


@login_required
def add_comment(request, id):
    if request.method == "POST":
        next_url = request.POST.get("next")
        post = get_object_or_404(Post, id=id)
        parent_id = request.POST.get("parent")
        body = (request.POST.get("body") or "").strip()
        if not body or len(body) > 1000:
            return HttpResponseBadRequest("Invalid comment body")

        with transaction.atomic():
            parent = None
            if parent_id:
                parent = get_object_or_404(Comment, id=parent_id, post=post)

            comment = Comment.objects.create(
                post=post, user=request.user, parent=parent, body=body
            )
            Post.objects.filter(id=id).update(comments_count=F("comments_count") + 1)
            if comment.parent_id:
                Comment.objects.filter(id=comment.parent_id).update(
                    replies_count=F("replies_count") + 1
                )
            return redirect(next_url)

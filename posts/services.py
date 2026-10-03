from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from django.db import transaction
from django.db.models import F
from .models import *


@login_required
def add_comment(request, id):
    if request.method == "POST":
        next_url = request.POST.get("next")
        post = get_object_or_404(Post, id=id)
        body = (request.POST.get("body") or "").strip()
        if not body:
            return HttpResponseBadRequest("Invalid comment body")

        with transaction.atomic():
            parent = None
            if parent_id := request.POST.get("parent"):
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
    return redirect("/")

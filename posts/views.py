from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Exists, F, OuterRef, Q
from django.views.decorators.http import require_POST
from .decorator import owner_ship_required
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import *

User = get_user_model()


def home(request):
    posts = (
        Post.objects.select_related("user")
        .prefetch_related(
            "media",
            Prefetch(
                "comments",
                Comment.objects.filter(parent=None)
                .select_related("user")
                .annotate(
                    is_liked=Exists(CommentLike.objects.filter(comment=OuterRef("id")))
                )
                .order_by("-likes_count")
                .prefetch_related(
                    Prefetch(
                        "replies",
                        Comment.objects.select_related("user").order_by("-created_at"),
                    )
                ),
                to_attr="none_parent_comment",
            ),
        )
        .annotate(is_liked=Exists(PostLike.objects.filter(post=OuterRef("id"))))
        .order_by("-like_count")
    )
    context = {"posts": posts}
    return render(request, "posts/home.html", context)


@login_required
def search(request):
    user = request.GET.get("u", "")
    get_users = None

    if user:
        get_users = User.objects.filter(Q(username__icontains=user)).exclude(
            username=request.user.username,
        )
    return render(request, "posts/search.html", {"get_users": get_users, "u": user})


@login_required
@owner_ship_required(Post, id_kwarg="id", user="user")
def delete_post(request, id):
    if request.method == "POST":
        get_object_or_404(Post, id=id).delete()
        return redirect(request.META.get("HTTP_REFERER"))
    return render(request, "posts/post-edit.html")


LIKE_MAP = {Post: (PostLike, "post"), Comment: (CommentLike, "comment")}


@login_required
@require_POST
def toggle_like_view(request, kind, id):
    model = {"post": Post, "comment": Comment}[kind]
    obj = get_object_or_404(model, id=id)
    next_url = request.POST.get("next")

    like_model, field = LIKE_MAP[type(obj)]
    with transaction.atomic():
        like, created = like_model.objects.get_or_create(
            user=request.user, **{field: obj}
        )
        if not created:
            like.delete()
        type(obj).objects.filter(id=obj.id).update(
            like_count=F("like_count") + (1 if created else -1)
        )

    return redirect(next_url)

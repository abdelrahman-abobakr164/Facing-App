from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Prefetch, Exists, F, OuterRef, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from .decorator import owner_ship_required
from django.db import transaction
from django.urls import reverse

from accounts.utils import people_you_may_know
from accounts.models import *

from .utils import post_commit
from .models import *

User = get_user_model()


@login_required
def home(request):
    following = Follow.objects.filter(
        follower=request.user, status="accepted"
    ).values_list("following_id")

    friends_requests = Follow.objects.filter(
        following=request.user, status="pending"
    ).select_related("follower")

    mutual_friends = people_you_may_know(request.user)

    posts = (
        Post.objects.filter(
            Q(user=request.user) | Q(user__in=following),
        )
        .select_related("user")
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
        .annotate(
            is_liked=Exists(
                PostLike.objects.filter(post=OuterRef("id"), user=request.user)
            )
        )
        .order_by("-created_at", "-like_count")
    )

    context = {
        "posts": posts,
        "friend_requests": friends_requests,
        "mutual_friends": mutual_friends,
    }
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
def edit_post(request, id):
    post = get_object_or_404(Post, id=id)
    media = PostMedia.objects.filter(post=post)

    if request.method == "POST":
        post_commit(request, id)
    return render(request, "posts/post-edit.html", {"post": post, "media": media})


@login_required
@owner_ship_required(Post, id_kwarg="id", user="user")
def delete_post(request, id):
    if request.method == "POST":
        next_url = request.POST.get("next")
        if not url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            if request.path == "profile":
                next_url = reverse("profile", args=[id])
            else:
                next_url = reverse("home")
        get_object_or_404(Post, id=id).delete()

    return redirect(next_url)


LIKE_MAP = {Post: (PostLike, "post"), Comment: (CommentLike, "comment")}


@login_required
@require_POST
def toggle_like_view(request, kind, id):
    model = {"post": Post, "comment": Comment}[kind]
    obj = get_object_or_404(model, id=id)

    next_url = request.POST.get("next")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        next_url = reverse("profile", args=[kind, id])

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

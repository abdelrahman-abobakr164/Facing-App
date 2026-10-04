from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Prefetch, Count, Exists, OuterRef
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from accounts.forms import SettingsForm
from posts.services import *
from posts.models import *
from .models import *

User = get_user_model()


@login_required
def settings(request):
    if request.method == "POST":
        form = SettingsForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("settings")
        else:
            return redirect("settings")
    else:
        form = SettingsForm(instance=request.user)

    return render(request, "accounts/settings.html", {"form": form})


@login_required
def profile(request, id):
    profile_user = get_object_or_404(User.objects.prefetch_related("followers"), id=id)
    posts = (
        Post.objects.filter(user=profile_user)
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
        .order_by("-created_at")
    )

    context = {
        "posts": posts,
        "profile_user": profile_user,
    }
    return render(request, "accounts/profile.html", context)


def connection(request, target):
    if request.method == "POST":
        next_url = request.POST.get("next", "/")
        target_user = User.objects.get(id=target)
        follow_status = Follow.objects.filter(
            follower=request.user, following=target_user
        ).select_related("follower", "following")

        if follow_status.exists():
            for i in follow_status:
                if i.status == "Pending":
                    return redirect(next_url)
                elif i.status == "Accepted":
                    return redirect(next_url)

        elif target_user.check_follower == True:
            status = "pending"
        else:
            status = "accepted"
        with transaction.atomic():
            if not follow_status.exists():
                Follow.objects.create(
                    follower=request.user, following=target_user, status=status
                )
            else:
                follow_status.delete()

        return redirect(next_url)
    else:
        return redirect(request.META.get("HTTP_REFERER"))


def connections(request, id):
    user = get_object_or_404(
        User.objects.prefetch_related("followers", "following"), id=id
    )
    followers = set(Follow.objects.filter(following=user).select_related('follower'))
    following = set(Follow.objects.filter(follower=user).select_related('following'))

    context = {"followers": followers, "following": following, "user": user}
    return render(request, "accounts/connections.html", context)

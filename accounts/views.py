from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Prefetch, Count, Exists, OuterRef
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse

from accounts.forms import SettingsForm
from .models import *
from .utils import *

from posts.services import *
from posts.models import *

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
    profile_user = get_object_or_404(
        User.objects.annotate(
            following_count=Count(
                "following", filter=Q(following__status="accepted"), distinct=True
            ),
            followers_count=Count(
                "followers", filter=Q(followers__status="accepted"), distinct=True
            ),
        ).prefetch_related("posts"),
        id=id,
    )
    follow_status = (
        Follow.objects.filter(follower=request.user, following=profile_user)
        .values_list("status", flat=True)
        .first()
    )

    if (
        follow_status == "accepted"
        or profile_user.is_private == False
        or request.user == profile_user
    ):
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
                        is_liked=Exists(
                            CommentLike.objects.filter(comment=OuterRef("id"))
                        )
                    )
                    .prefetch_related(
                        Prefetch(
                            "replies",
                            Comment.objects.select_related("user").order_by(
                                "-created_at"
                            ),
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
    else:
        posts = []

    context = {
        "posts": posts,
        "follow_status": follow_status,
        "profile_user": profile_user,
    }
    return render(request, "accounts/profile.html", context)


@login_required
@require_POST
def connection(request, target):
    if request.method == "POST":
        next_url = request.POST.get("next", "/")
        action = request.POST.get("action")
        if not url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            next_url = reverse("profile", args=[target])

        target_user = User.objects.get(id=target)

        if action:
            if action == "remove":
                Follow.objects.filter(follower=target, following=request.user).delete()

        else:
            follow_status = Follow.objects.filter(
                follower=request.user, following=target_user
            )
            pending_requests = Follow.objects.filter(
                following=request.user, follower=target_user, status="pending"
            )
            pending_sent = Follow.objects.filter(
                follower=request.user, following=target_user, status="pending"
            )

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
                if pending_requests.exists():
                    accept = pending_requests.first()
                    accept.status = "accepted"
                    accept.save()
                elif pending_sent.exists():
                    pending_sent.delete()
                elif not follow_status.exists():
                    Follow.objects.create(
                        follower=request.user, following=target_user, status=status
                    )

                else:
                    follow_status.delete()

        return redirect(next_url)
    else:
        return redirect(request.META.get("HTTP_REFERER"))


@login_required
def connections(request, id):
    user = get_object_or_404(
        User.objects.prefetch_related("followers", "following"), id=id
    )
    followers = (
        Follow.objects.filter(following=user, status="accepted")
        .select_related("follower")
        .annotate(
            follower_following=Count("follower__following"),
            follower_followers=Count("follower__followers"),
        )
    )

    following = (
        Follow.objects.filter(follower=user, status="accepted")
        .select_related("following")
        .annotate(
            following_following=Count("following__following"),
            following_followers=Count("following__followers"),
        )
    )

    user_pending_ids = set(
        Follow.objects.filter(follower=request.user, status="pending").values_list(
            "following_id", flat=True
        )
    )
    user_accepted_ids = set(
        Follow.objects.filter(follower=request.user, status="accepted").values_list(
            "following_id",
            flat=True,
        )
    )

    context = {
        "followers": followers,
        "following": following,
        "user": user,
        "user_pending_ids": user_pending_ids,
        "user_accepted_ids": user_accepted_ids,
    }
    return render(request, "accounts/connections.html", context)


@login_required
def requests(request):
    friends_requests = Follow.objects.filter(
        following=request.user, status="pending"
    ).select_related("follower")

    sent_requests = Follow.objects.filter(
        follower=request.user, status="pending"
    ).select_related("following")

    mutual_friends = mutuals_count(request, friends_requests)
    related_people = people_you_may_know(request.user)

    context = {
        "friend_requests": friends_requests,
        "sent_requests": sent_requests,
        "mutual_friends": mutual_friends,
        "related_people": related_people,
    }
    return render(request, "accounts/requests.html", context)

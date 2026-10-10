from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Follow

User = get_user_model()


def mutuals_count(request, friends_requests):
    mutual_follow = Follow.objects.filter(
        Q(follower=request.user, status=Follow.Status.ACCEPTED)
        | Q(following=request.user, status=Follow.Status.ACCEPTED)
    )

    mutual_list = set()
    for f in friends_requests:
        for i in mutual_follow:
            if i.follower_id != request.user.id and i.follower_id != f.follower_id:
                mutual_list.add(i.follower_id)
            if i.following_id != request.user.id and i.follower_id != f.following_id:
                mutual_list.add(i.following_id)

    return User.objects.filter(id__in=mutual_list)


def people_you_may_know(user):
    follow_set = set()
    mutual_list = set()

    UIfollowing = user.following.values_list("following_id", flat=True)
    Mfollowers = user.followers.values_list("follower_id", flat=True)

    for i in UIfollowing:
        follow_set.add(i)
    for i in Mfollowers:
        follow_set.add(i)

    mutual_followers = (
        Follow.objects.filter(
            Q(following__in=Mfollowers, status=Follow.Status.ACCEPTED)
            | Q(follower__in=Mfollowers, status=Follow.Status.ACCEPTED)
        )
        .exclude(follower=user)
        .exclude(following=user)
    )

    mutual_following = (
        Follow.objects.filter(
            Q(follower__in=UIfollowing, status=Follow.Status.ACCEPTED)
            | Q(following__in=UIfollowing, status=Follow.Status.ACCEPTED)
        )
        .exclude(follower=user)
        .exclude(following=user)
    )

    for i in mutual_followers:
        if i.follower.id not in follow_set:
            mutual_list.add(i.follower.id)
        if i.following.id not in follow_set:
            mutual_list.add(i.following.id)

    for i in mutual_following:
        if i.follower.id not in follow_set:
            mutual_list.add(i.follower.id)
        if i.following.id not in follow_set:
            mutual_list.add(i.following.id)

    return User.objects.filter(id__in=mutual_list)

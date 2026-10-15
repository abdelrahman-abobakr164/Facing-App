from django.contrib.auth import get_user_model
from collections import defaultdict
from django.db.models import Q

from .models import Follow

User = get_user_model()


def _friend_map(user_ids):
    friends = defaultdict(set)
    pairs = (
        Follow.objects.filter(status=Follow.Status.ACCEPTED)
        .filter(Q(follower_id__in=user_ids) | Q(following_id__in=user_ids))
        .values_list("follower_id", "following_id")
    )
    for follower_id, following_id in pairs:
        if follower_id in user_ids:
            friends[follower_id].add(following_id)
        if following_id in user_ids:
            friends[following_id].add(follower_id)
    return friends


def mutuals_count(request, friends_requests):
    me = request.user.id
    requester_ids = {f.follower_id for f in friends_requests}

    friends = _friend_map(requester_ids | {me})
    my_friends = friends[me]

    return {rid: len(friends[rid] & my_friends) for rid in requester_ids}


def people_you_may_know(user):
    following_ids = set(user.following.values_list("following_id", flat=True))
    follower_ids = set(user.followers.values_list("follower_id", flat=True))

    direct_network = following_ids | follower_ids

    related_follows = (
        Follow.objects.filter(status=Follow.Status.ACCEPTED)
        .filter(Q(following_id__in=direct_network) | Q(follower_id__in=direct_network))
        .exclude(Q(follower_id=user.id) | Q(following_id=user.id))
        .values_list("follower_id", "following_id")
    )

    MutualList = set()

    for follower_id, following_id in related_follows:
        if follower_id not in direct_network:
            MutualList.add(follower_id)
        if following_id not in direct_network:
            MutualList.add(following_id)

    return User.objects.filter(id__in=MutualList)

from django.shortcuts import redirect, get_object_or_404
from django.db import transaction
from django.db.models import Exists, F, OuterRef
from .models import *

LIKE_MAP = {Post: (PostLike, "post"), Comment: (CommentLike, "comment")}


def toggle_like(user, obj):
    like_model, field = LIKE_MAP[type(obj)]
    with transaction.atomic():
        like, created = like_model.objects.get_or_create(user=user, **{field: obj})
        if not created:
            like.delete()
        type(obj).objects.filter(pk=obj.pk).update(
            likes_count=F("likes_count") + (1 if created else -1)
        )
    return created



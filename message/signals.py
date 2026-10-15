from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Count
from accounts.models import Follow
from .models import Conversation


@receiver(post_save, sender=Follow)
def create_conversation_after_follow(sender, instance, **kwargs):
    if instance.status != Follow.Status.ACCEPTED:
        return
    user_a, user_b = instance.follower_id, instance.following_id

    exists = (
        Conversation.objects.annotate(n=Count("participants"))
        .filter(n=2)
        .filter(participants=user_a)
        .filter(participants=user_b)
        .exists()
    )
    if exists:
        return
    
    with transaction.atomic():
        conversation = Conversation.objects.create()
        conversation.participants.add(user_a, user_b)

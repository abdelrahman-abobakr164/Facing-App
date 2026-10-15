from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Story


def _delete_from_storage(storage, name):
    if name:
        transaction.on_commit(lambda: storage.delete(name))


@receiver(post_delete, sender=Story)
def delete_story_file(sender, instance, **kwargs):
    if instance.media:
        _delete_from_storage(instance.media.storage, instance.media.name)

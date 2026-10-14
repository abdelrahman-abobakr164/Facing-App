from django.db.models import Q, Exists, OuterRef, Prefetch, When, Case, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model

from .models import *

User = get_user_model()


def lobby(request):
    message = Message.objects.filter(conversation__participants=request.user)
    conversations = (
        Conversation.objects.filter(participants=request.user)
        .prefetch_related(
            "participants",
            Prefetch(
                "messages",
                message.prefetch_related(Prefetch("attachments")).order_by("timestamp"),
                "messages_filter",
            ),
        )
        .annotate(
            unread_count=Case(
                When(
                    is_group=False,
                    then=Count(
                        "messages",
                        filter=Q(messages__read=False)
                        & ~Q(messages__sender=request.user),
                        distinct=True,
                    ),
                ),
                When(
                    is_group=True,
                    then=Count(
                        "messages",
                        filter=Q(messages__read=False)
                        & ~Q(messages__read_by=request.user),
                        distinct=True,
                    ),
                ),
            ),
            readed=Exists(
                Message.objects.filter(read=True, conversation=OuterRef("id"))
            ),
        )
    )

    context = {
        "conversations": conversations,
    }
    return render(request, "messages/lobby.html", context)


def group(request, id=None):
    return render(request, "messages/group.html")


def chat_room(request, id):
    return render(request, "messages/chat.html")

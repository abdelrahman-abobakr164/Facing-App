from django.db.models import Q, Exists, OuterRef, Prefetch, When, Case, Count, F
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import transaction

from .models import *
from .forms import *
from accounts.models import Follow
from posts.utils import get_safe_next_url

User = get_user_model()


@login_required
def lobby(request):
    message = Message.objects.filter(
        conversation__participants=request.user
    ).select_related("sender")
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
                Message.objects.filter(
                    read=True, sender=request.user, conversation=OuterRef("id")
                )
            ),
        )
    )

    context = {
        "conversations": conversations,
    }
    return render(request, "messages/lobby.html", context)


def mark_seen(request, user, id):
    conv = get_object_or_404(Conversation, id=id)
    with transaction.atomic():
        if conv.is_group:
            msgs = Message.objects.filter(conversation=conv).exclude(
                sender=request.user
            )
            for msg in msgs:
                msg.mark_as_read_by_user(request.user)
        else:
            msgs = Message.objects.filter(
                conversation=conv, read=False, sender=user
            ).update(read=F("read") + True)
    return msgs


@login_required
def chat_room(request, id):
    conversation = get_object_or_404(Conversation, id=id)
    mark_seen(request, conversation.other_participants(request.user), id)

    msgs = (
        Message.objects.filter(conversation=conversation)
        .select_related("sender")
        .prefetch_related(Prefetch("attachments", MessageAttachment.objects.all()))
    )
    if conversation.is_group:
        name = conversation.group_name
    else:
        name = conversation.other_participants(request.user)

    context = {"conversation": conversation, "msgs": msgs, "name": name}
    return render(request, "messages/chat.html", context)


@login_required
def group(request, id=None):
    next_url = get_safe_next_url(request)
    followers = Follow.objects.filter(
        Q(following=request.user, status=Follow.Status.ACCEPTED)
    ).values_list("follower_id", flat=True)
    following = Follow.objects.filter(
        Q(follower=request.user, status=Follow.Status.ACCEPTED)
    ).values_list("following_id", flat=True)

    follow_set = set()

    for i in followers:
        if Follow.objects.filter(
            following=i, follower=request.user, status=Follow.Status.ACCEPTED
        ).exists():
            follow_set.add(i)

    for i in following:
        if Follow.objects.filter(
            follower=i, following=request.user, status=Follow.Status.ACCEPTED
        ).exists():
            follow_set.add(i)

    users = User.objects.filter(id__in=follow_set)

    conversation = None

    if id:
        conversation = get_object_or_404(Conversation, id=id)
        following.exclude(following__in=conversation.participants.all())
        if request.user not in conversation.admin.all():
            return redirect(next_url)
        form = GroupForm(request.POST, request.FILES, instance=conversation)
    else:
        form = GroupForm(request.POST, request.FILES)

    if request.method == "POST":
        with transaction.atomic():
            if form.is_valid():
                group = form.save(commit=False)
                group.is_group = True
                group.save()
                form.save_m2m()
                group.participants.add(request.user)
                group.admin.add(request.user)
                messages.success(request, f"{form.cleaned_data['group_name']} has been created Successfully!")
                return redirect("lobby")

            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")

        return redirect(next_url)

    context = {"form": form, "users": users, "conv": conversation}
    return render(request, "messages/group.html", context)


@login_required
def delete_group(request, id):
    conv = get_object_or_404(Conversation, id=id)
    if request.user in conv.admin.all():
        conv.delete()

    return redirect(("lobby"))


@login_required
def leave(request, id):
    conv = get_object_or_404(Conversation, id=id)
    with transaction.atomic():
        if conv.admin.all() == request.user:
            conv.delete()
        else:
            conv.participants.remove(request.user)
            if request.user in conv.admin.all():
                conv.admin.remove(request.user)
    return redirect(("lobby"))


@login_required
def delete_chat(request, id):
    next_url = get_safe_next_url(request)
    Message.objects.get(id=id).delete()
    return redirect(next_url)

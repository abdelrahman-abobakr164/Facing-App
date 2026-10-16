from django.db.models import Q, Exists, OuterRef, Prefetch, When, Case, Count, F, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import transaction

from .models import *
from .forms import *
from accounts.models import Follow
from posts.utils import get_safe_next_url
from posts.decorator import owner_ship_required

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
            latest_messages=Max("messages__timestamp"),
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
                        & ~Q(messages__read_by=request.user)
                        & ~Q(messages__sender=request.user),
                        distinct=True,
                    ),
                ),
            ),
            readed=Exists(
                Message.objects.filter(
                    read=True,
                    sender=request.user,
                    conversation=OuterRef("id"),
                )
            ),
        )
        .order_by("-latest_messages")
        .distinct()
    )

    context = {"conversations": conversations}
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
    conv = get_object_or_404(Conversation, id=id)

    other_user = conv.other_participants(request.user)

    if request.user not in conv.participants.all():
        return redirect("lobby")

    exists_follow = Follow.objects.filter(
        Q(follower=request.user, following=other_user)
        | Q(following=request.user, follower=other_user),
        status=Follow.Status.ACCEPTED,
    )

    btn = False
    if not exists_follow.exists():
        btn = True
        messages.warning(request, "You're not friends any more")

    mark_seen(request, conv.other_participants(request.user), id)

    msgs = (
        Message.objects.filter(conversation=conv)
        .select_related("sender", "conversation")
        .prefetch_related(Prefetch("attachments", MessageAttachment.objects.all()))
        .order_by("timestamp")
    )
    if conv.is_group:
        name = conv.group_name
    else:
        name = conv.other_participants(request.user)

    if request.method == "POST":
        next_url = get_safe_next_url(request)
        form = MessageForm(request.POST, request.FILES)
        with transaction.atomic():
            if form.is_valid():
                form.save(request.user, conv)
                return redirect(next_url)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return redirect(next_url)

    context = {"conversation": conv, "msgs": msgs, "name": name, "btn": btn}
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
                messages.success(
                    request,
                    f"{form.cleaned_data['group_name']} has been created Successfully!",
                )
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
def delete_chat(request, conv_id, id):
    Message.objects.get(id=id).delete()
    return redirect("chat", id=conv_id)


@login_required
@owner_ship_required(Message, id_kwarg="id", user="sender")
def chat_info(request, id):
    Message.objects.prefetch_related("read_by").get(id=id)
    return render(request, "messages/info.html")

from django.urls import path
from . import views

urlpatterns = [
    path("", views.lobby, name="lobby"),
    path("group/", views.group, name="group"),
    # path("block-chats/", views.block, name="block"),
    # path("leave-group/<uuid:pk>/", views.leave, name="leave"),
    # path("delete-group/<uuid:pk>/", views.delete_group, name="delete-group"),
    # path("delete/<uuid:pk>/", views.delete_chat, name="delete-chat"),
    path("group/<uuid:id>/", views.group, name="group_edit"),
    path("<uuid:pk>/", views.chat_room, name="chat"),
]

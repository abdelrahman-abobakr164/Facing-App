from django.urls import path
from . import views

urlpatterns = [
    path("", views.lobby, name="lobby"),
    path("group/", views.group, name="group"),
    path("leave/<uuid:id>/", views.leave, name="leave"),
    path("delete-group/<uuid:id>/", views.delete_group, name="delete-group"),
    path("delete/<uuid:conv_id>/<uuid:id>/", views.delete_chat, name="delete-chat"),
    path("group/<uuid:id>/", views.group, name="group_edit"),
    path("<uuid:id>/", views.chat_room, name="chat"),
    path("details/<uuid:id>/", views.chat_info, name="info"),
]

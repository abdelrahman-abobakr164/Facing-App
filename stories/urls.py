from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create, name="create_story"),
    path("<uuid:id>/viewers/", views.viewers, name="viewers"),
    path("<uuid:id>/like/", views.like, name="like_story"),
    path("<uuid:id>/delete/", views.delete, name="delete_story"),
    path("<uuid:id>/", views.viewer, name="viewer"),
]

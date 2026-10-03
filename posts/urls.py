from django.urls import path
from .services import *
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("people/", views.search, name="search"),
    path("d/post/<uuid:id>/", views.delete_post, name="delete_post"),
    path("a/comment/<uuid:id>/", add_comment, name="add_comment"),
    path("<str:kind>/<uuid:id>/like/", views.toggle_like_view, name="toggle-like"),
]

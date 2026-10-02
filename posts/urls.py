from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("d/post/<uuid:id>/", views.delete_post, name="delete_post"),
    path("a/comment/<uuid:id>/", views.add_comment, name="add_comment"),
]

from django.urls import path
from . import views

urlpatterns = [
    path("profile/<uuid:id>/", views.profile, name="profile"),
    path("settings/", views.settings, name="settings"),
]

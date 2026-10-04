from django.urls import path
from . import views

urlpatterns = [
    path("settings/", views.settings, name="settings"),
    path("connections/<uuid:id>/", views.connections, name="connections"),
    path("profile/<uuid:id>/", views.profile, name="profile"),
    path("connection/<uuid:target>/", views.connection, name="connection"),
]

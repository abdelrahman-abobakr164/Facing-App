from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/conversation/<uuid:conversation_id>/", consumers.ChatConsumer.as_asgi())
]

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        # is_participant = await
        
    async def disconnect(self, close_code):
        await super().disconnect(close_code)

    async def receive_json(self, content, **kwargs):
        return await super().receive_json(content, **kwargs)

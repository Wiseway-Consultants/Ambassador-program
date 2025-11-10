from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        query_string = self.scope["query_string"].decode()
        token = None

        if "token=" in query_string:
            token = query_string.split("token=")[-1]

        self.user = await self.authenticate_user(token)

        if self.user:
            await self.accept()
            await self.channel_layer.group_add(f"user_{self.user.id}", self.channel_name)
            print(f"✅ Connected: {self.user.email}")
        else:
            print("❌ Invalid or expired token")
            await self.close()

    @database_sync_to_async
    def authenticate_user(self, token):
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import AccessToken, TokenError
        user = get_user_model()
        if not token:
            return None
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return user.objects.get(id=user_id)
        except (TokenError, user.DoesNotExist):
            return None

    async def disconnect(self, code):
        if self.user:
            await self.channel_layer.group_discard(f"user_{self.user.id}", self.channel_name)

    async def send_notification(self, event):
        # Called when notification sent via channel_layer.group_send
        await self.send_json({
            "type": "notification",
            "message": event["message"],
            "title": event["title"],
            "notification_type": event["notification_type"],
        })
        print("Notification sent to websocket")

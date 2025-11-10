from django.db import models
from django.conf import settings


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=64, default="Ambassador")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=10)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user}: {self.message}"


class PushNotificationDeviceToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fcmDeviceTokens')
    push_token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FCM Token for: {self.user}"

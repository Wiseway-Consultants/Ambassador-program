from rest_framework import serializers

from notifications.models import Notification, PushNotificationDeviceToken


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "created_at", "notification_type", "read"]


class PushNotificationDeviceTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = PushNotificationDeviceToken
        fields = ["push_token", "device_type", "created_at"]

import logging
from os import getenv

import requests
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db import transaction
from dotenv import load_dotenv

from notifications.models import Notification, PushNotificationDeviceToken

load_dotenv()
logger = logging.getLogger(__name__)


def send_push_notification(push_token, title, message, data=None):
    payload = {
        'to': push_token,
        'title': title,
        'body': message,
        'data': data or {},
        'sound': 'default',
        'priority': 'high'
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    response = requests.post('https://exp.host/--/api/v2/push/send', json=payload, headers=headers)
    logger.info(f"Push Notification sent response: {response.json()}")
    return response.json()


def push_notify_user(user_id, title, message):
    tokens = PushNotificationDeviceToken.objects.filter(user_id=user_id).values_list('push_token', flat=True)
    logger.info(f"User {user_id} push notification tokens: {len(tokens)}")
    for token in tokens:
        send_push_notification(token, title, message)


def send_notification(user_id, message, notification_type, notification_title):
    with transaction.atomic():
        Notification.objects.create(
            user_id=user_id,
            message=message,
            title=notification_title,
            notification_type=notification_type
        )
        logger.info("Notification created in DB")
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "send_notification",
                "message": message,
                "title": notification_title,
                "notification_type": notification_type
            },
        )
        push_notify_user(user_id, message, notification_title)

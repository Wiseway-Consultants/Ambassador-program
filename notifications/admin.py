from django.contrib import admin

from notifications.models import Notification, PushNotificationDeviceToken


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "created_at",
        "message"
    )
    list_filter = ("created_at", "user", "created_at")
    search_fields = ("user", "prospect")
    readonly_fields = ("created_at",)


@admin.register(PushNotificationDeviceToken)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "created_at",
        "push_token",
        "device_type"
    )
    list_filter = ("created_at", "user", "created_at")
    search_fields = ("user",)
    readonly_fields = ("created_at",)

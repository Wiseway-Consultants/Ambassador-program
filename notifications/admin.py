from django.contrib import admin

from notifications.models import Notification


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

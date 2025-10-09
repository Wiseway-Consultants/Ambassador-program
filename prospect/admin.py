from django.contrib import admin
from .models import Prospect


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "phone",
        "country",
        "invited_by_user",
        "registered_user",
        "created_at",
    )
    list_filter = ("created_at", "invited_by_user", "country")
    search_fields = ("email", "phone")
    autocomplete_fields = ("invited_by_user", "registered_user")
    readonly_fields = ("created_at",)

    # Optional: to show clickable links for related users
    def invited_by_user_link(self, obj):
        if obj.invited_by_user:
            return f"{obj.invited_by_user.email}"
        return "-"
    invited_by_user_link.short_description = "Invited By"

    def registered_user_link(self, obj):
        if obj.registered_user:
            return f"{obj.registered_user.email}"
        return "-"
    registered_user_link.short_description = "Registered User"

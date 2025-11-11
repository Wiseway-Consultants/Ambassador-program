from django.contrib import admin

from commission.models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = (
        "prospect",
        "user",
        "commission_tree_level",
        "number_of_frylows",
        "money_amount",
        "created_at",
        "updated_at"
    )
    list_filter = ("created_at", "user", "prospect")
    search_fields = ("user", "prospect")
    readonly_fields = ("created_at", "updated_at")

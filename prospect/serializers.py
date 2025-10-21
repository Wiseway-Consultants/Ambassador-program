from rest_framework import serializers

from prospect.models import Prospect


class ProspectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prospect
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "country",
            "comments",
            "contact_name",
            "restaurant_organisation_name",
            "invited_by_user",
            "ghl_contact_id",
            "ghl_opportunity_id",
            "deal_completed",
            "created_at"
        )
        read_only_fields = ("invited_by_user", "deal_completed", "created_at", "ghl_contact_id", "ghl_opportunity_id")

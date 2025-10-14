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
            "deal_completed",
            "created_at"
        )
        read_only_fields = ("deal_completed", "created_at")

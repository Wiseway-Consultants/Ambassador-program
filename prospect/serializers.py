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
            "invited_by_user",
            "registered_user",
        )
        read_only_fields = ("invited_by_user", "registered_user", "deal_completed")

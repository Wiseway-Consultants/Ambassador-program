from rest_framework import serializers

from prospect.models import Prospect


class ProspectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prospect
        fields = (
            "email",
            "phone",
            "invited_by_user",
            "registered_user",
        )
        read_only_fields = ("invited_by_user", "registered_user")

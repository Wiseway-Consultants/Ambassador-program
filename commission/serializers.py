from rest_framework import serializers

from commission.models import Commission
from prospect.serializers import ProspectSerializer


class CommissionListSerializer(serializers.ModelSerializer):
    prospect = ProspectSerializer(read_only=True)

    class Meta:
        model = Commission
        fields = [
            "id",
            "prospect",
            "number_of_frylows",
            "created_at",
            "updated_at",
        ]
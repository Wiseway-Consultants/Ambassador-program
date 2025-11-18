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
            "user",
            "number_of_frylows",
            "currency",
            "money_amount",
            "created_at",
            "updated_at",
            "paid",
            "stripe_transfer_id"
        ]
        read_only_fields = ["created_at", "updated_at", "paid", "stripe_transfer_id", "money_amount", "currency"]


class CommissionStripePayoutSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def validate_id(self, value):
        try:
            commission = Commission.objects.get(id=value)
        except Commission.DoesNotExist:
            raise serializers.ValidationError(f"Commission with id {value} does not exist.")
        if commission.paid:
            raise serializers.ValidationError(f"Commission with id {value} is already paid.")
        if not commission.user.stripe_onboard_status:
            raise serializers.ValidationError(f"This ambassador is not onboarded for Stripe payouts.")
        return value

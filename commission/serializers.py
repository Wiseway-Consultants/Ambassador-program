from rest_framework import serializers

from commission.models import Commission


class CommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commission
        fields = '__all__'
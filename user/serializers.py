from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer


class TokenObtainPairSerializer(JwtTokenObtainPairSerializer):
    username_field = get_user_model().USERNAME_FIELD


class UserSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Optional referral code to link accounts."
    )

    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "currency",
            "is_accepted_terms",
            "referral_code",
        )
        extra_kwargs = {
            "password": {
                "write_only": True,
                "required": False,
                "help_text": "Required for account creation."
            },
            "email": {
                "help_text": "The user's email address. Must be unique."
            },
            "first_name": {
                "help_text": "The user's first name."
            },
            "last_name": {
                "help_text": "The user's last name."
            },
            "phone": {
                "help_text": "The user's phone number."
            },
            "currency": {
                "help_text": "The preferred currency for the user's account."
            },
            "is_accepted_terms": {
                "help_text": "Boolean indicating if the user has accepted the terms and conditions."
            },
        }

    def create(self, validated_data):
        referral_code = validated_data.pop("referral_code", None)
        return get_user_model().objects.create_user(
            referral_code=referral_code,
            **validated_data
        )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

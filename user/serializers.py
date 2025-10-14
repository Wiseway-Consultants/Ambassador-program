from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer


class TokenObtainPairSerializer(JwtTokenObtainPairSerializer):
    username_field = get_user_model().USERNAME_FIELD


class UserSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(required=False)

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
            "is_staff",
            "is_superuser"
        )
        extra_kwargs = {
            "password": {
                "write_only": True,
                "required": False,
            },
            "is_staff": {
                "read_only": True,
                "required": False,
            },
            "is_superuser": {
                "read_only": True,
                "required": False,
            }
        }

    def create(self, validated_data):
        return get_user_model().objects.create_user(
            **validated_data
        )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

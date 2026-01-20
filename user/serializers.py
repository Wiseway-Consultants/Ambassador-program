import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer


logger = logging.getLogger(__name__)


class TokenObtainPairSerializer(JwtTokenObtainPairSerializer):
    username_field = get_user_model().USERNAME_FIELD


class InvitedByUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name")


class UserSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True
    )
    invited_by_user = InvitedByUserSerializer(read_only=True)
    invited_by_user_id = serializers.IntegerField(write_only=True, required=False)

    has_usable_password = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "currency",
            "invited_by_user",
            "invited_by_user_id",
            "organization_name",
            "is_accepted_terms",
            "referral_code",
            "is_staff",
            "is_superuser",
            "has_usable_password",
            "skip_invitation_code_input"
        )

        read_only_fields = ("id", "is_staff", "is_superuser", "has_usable_password")

        extra_kwargs = {
            "password": {
                "write_only": True,
                "required": False,
            }
        }

    def get_has_usable_password(self, obj):
        return obj.has_usable_password()

    def create(self, validated_data):
        referral_code = validated_data.pop("referral_code", None)
        if referral_code == "":
            referral_code = None
        return get_user_model().objects.create_user(
            referral_code=referral_code,
            **validated_data
        )


class AdminUserSerializer(serializers.ModelSerializer):
    is_invited_by_rm = serializers.BooleanField(read_only=True)
    invited_by_user = UserSerializer(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "currency",
            "invited_by_user",
            "organization_name",
            "referral_code",
            "is_staff",
            "is_superuser",
            "is_invited_by_rm"
        )

        read_only_fields = ("id", "is_staff", "is_superuser")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=False)
    new_password = serializers.CharField(required=True, validators=[validate_password])

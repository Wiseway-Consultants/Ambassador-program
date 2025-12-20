import logging
import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from notifications.utils import send_notification
from prospect.models import Prospect
from utils.send_email import send_notification_email

logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, phone, password=None, referral_code=None, **extra_fields):
        if not email or not phone:
            raise ValueError(_('Email and Phone must be set'))

        email = self.normalize_email(email)

        inviter_user = None

        prospect = Prospect.objects.filter(Q(email=email) | Q(phone=phone)).first()
        # CASE A: inviter from referral code
        if referral_code:
            inviter_user = User.objects.filter(referral_code=referral_code).first()
            logger.info(f"User: {inviter_user} is referring to prospect")

        # CASE B: user existed as prospect
        if prospect:
            inviter_user = prospect.invited_by_user

        user = self.model(email=email, phone=phone, **extra_fields)

        if prospect:
            user.is_prospect = True

        # link referral
        if inviter_user:
            user.invited_by_user = inviter_user
            # Send email notification to User who invited this ambassador
            send_notification_email(to_user=inviter_user, notification_object=user, notification_type="user")
            send_notification(
                inviter_user.id,
                f"New Ambassador: {user.first_name} {user.last_name}\n"
                f"register using you referral code",
                "info",
                "Your new Ambassador",
            )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        logger.info(f"User created: {user}")

        user.save()
        if prospect:
            prospect.registered_user = user
            prospect.save()

        return user

    def create_superuser(self, email, password, phone=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, phone, password, **extra_fields)


class User(AbstractUser):
    username = None

    invited_by_user = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_users"
    )

    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=30)
    phone = models.CharField(_('phone number'), max_length=30, blank=True)
    currency = models.CharField(_('currency'), max_length=3)
    organization_name = models.CharField(_('organization name'), max_length=128, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_accepted_terms = models.BooleanField(default=False)
    is_prospect = models.BooleanField(default=False)
    referral_code = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)  # Will be used for unique QRcode
    referral_qr_code_id = models.CharField(max_length=10, blank=True)
    qr_code_bundles = models.JSONField(default=dict, blank=True, null=False)

    stripe_account_id = models.CharField(max_length=128, blank=True, null=True)
    stripe_onboard_status = models.BooleanField(default=False)
    apple_user_id = models.CharField(max_length=64, unique=True, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "phone",
        "currency"
    ]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

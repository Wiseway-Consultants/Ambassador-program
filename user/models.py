import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password=None, referral_code=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))

        email = self.normalize_email(email)

        # If parent_id is provided, fetch the User instance
        parent = None
        if referral_code:
            try:
                parent = self.model.objects.get(referral_code=referral_code)
            except self.model.DoesNotExist:
                raise ValueError(_('Parent user does not exist'))

        user = self.model(email=email, parent=parent, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
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
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None

    # Referral tracking
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children"
    )
    parent_path = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True
    )

    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=30)
    phone = models.CharField(_('phone number'), max_length=30, blank=True)
    currency = models.CharField(_('currency'), max_length=3)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_accepted_terms = models.BooleanField(default=False)
    referral_code = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)  # Will be used for unique QRcode
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "phone",
        "currency"
    ]

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.parent:
            self.parent_path = self.parent.parent_path + [self.parent.id]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

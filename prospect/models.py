from django.db import models
from django.conf import settings


class Prospect(models.Model):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=11)

    invited_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prospects",
        null=True,
        blank=True
    )

    registered_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prospect_profile"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

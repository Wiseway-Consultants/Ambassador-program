from django.conf import settings
from django.db import models

from prospect.models import Prospect


class Commission(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    prospect = models.ForeignKey(
        Prospect,
        on_delete=models.CASCADE,
        related_name='commissions',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="commissions",
        null=False,
        blank=False
    )
    commission_tree_level = models.PositiveSmallIntegerField()
    number_of_frylows = models.PositiveIntegerField()
    money_amount = models.FloatField(default=0)
    currency = models.CharField(max_length=10, blank=True, null=True)


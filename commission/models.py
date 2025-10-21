from django.db import models

from prospect.models import Prospect


class Commission(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    prospect = models.OneToOneField(Prospect, on_delete=models.CASCADE)
    number_of_frylows = models.IntegerField(default=0)

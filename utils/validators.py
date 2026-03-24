import re
from django.core.exceptions import ValidationError


def validate_human_name(value):
    # Must contain only letters, spaces, hyphens, apostrophes
    if not re.match(r"^[A-Za-zÀ-ÿ\s\-'.]+$", value):
        raise ValidationError("Name looks suspicious. Please contact hello@savefryoil.com for assistance.")

    # Reject if too long (real names rarely exceed 50 chars)
    if len(value) > 50:
        raise ValidationError("Invalid name. Name is too long.")

    # Detect gibberish: too many consecutive consonants
    consonant_clusters = re.findall(r'[^aeiouAEIOU\s]{5,}', value)
    if consonant_clusters:
        raise ValidationError("Name looks suspicious. Please contact hello@savefryoil.com for assistance.")

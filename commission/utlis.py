import stripe
from django.conf import settings

from prospect.utils import get_country_code_by_currency
from user.models import User

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_express_account(user: User):
    country = get_country_code_by_currency(user.currency)
    account = stripe.Account.create(
        type="express",
        country=country,
        email=user.email,
        capabilities={
            "card_payments": {"requested": True},
            "transfers": {"requested": True}
        }
    )
    print(f"Stripe response: {account}")
    user.stripe_account_id = account.id
    user.save()
    return account.id

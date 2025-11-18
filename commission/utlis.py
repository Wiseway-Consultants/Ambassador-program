import logging

import requests
import stripe
from django.conf import settings

from commission.models import Commission
from prospect.utils import get_country_code_by_currency
from user.models import User

STRIPE_SECRET_KEY = settings.STRIPE_SECRET_KEY
stripe.api_key = STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

STRIPE_FINANCIAL_ACCOUNT = settings.STRIPE_FINANCIAL_ACCOUNT
STRIPE_FINANCIAL_ACCOUNT_CURRENCY = settings.STRIPE_FINANCIAL_ACCOUNT_CURRENCY
HEADERS = {
            "Stripe-Version": "2025-10-29.preview",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {STRIPE_SECRET_KEY}"
        }


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


def create_stripe_transfer(user: User, commission: Commission):
    money_amount_in_cents = int(commission.money_amount * 100)
    transfer_currency = commission.currency
    user_express_account = user.stripe_account_id
    transfer = stripe.Transfer.create(
        amount=money_amount_in_cents,  # amount in cents, e.g. $50.00
        currency=transfer_currency,
        destination=user_express_account,
        transfer_group="payout_001"
    )
    return transfer


def retrieve_recipient_stripe(user: User):
    recipient_id = user.stripe_account_id
    url = f"https://api.stripe.com/v2/core/accounts/{recipient_id}?include=configuration.recipient"

    response = requests.get(
        url,
        headers=HEADERS
    )

    logger.info(f"Retrieve stripe recipient account for user {user.id}: {response.json()}")
    return response.json()


def create_stripe_recipient(user: User):
    name = f"{user.first_name} {user.last_name}"
    country = get_country_code_by_currency(user.currency)

    url = "https://api.stripe.com/v2/core/accounts"

    data = {
        "configuration": {
            "recipient": {
                "capabilities": {
                    "bank_accounts": {
                        "local": {
                            "requested": True
                        }
                    }
                }
            }
        },
        "contact_email": user.email,
        "display_name": name,
        "identity": {
            "country": country,
            "entity_type": "individual"
        },
        "include": [
            "identity",
            "configuration.recipient",
            "requirements"
        ]
    }

    response = requests.post(
        url,
        json=data,
        headers=HEADERS
    )

    logger.info(f"Stripe recipient response: {response.json()}")
    if not response.status_code == 200:
        raise Exception(f"Stripe recipient error: {response.json()}")
    return response.json()["id"]


def create_bank_account_link(recipient_id: str):
    url = "https://api.stripe.com/v2/core/account_links"

    data = {
        "account": recipient_id,
        "use_case": {
            "type": "account_onboarding",
            "account_onboarding": {
                "configurations": [
                    "recipient"
                ],
                "return_url": "https://savefryoil.com/ambassador-referrals/claimed-commissions/",
                "refresh_url": "https://savefryoil.com/ambassador-referrals/claimed-commissions/"
            }
        }
    }

    response = requests.post(
        url,
        json=data,
        headers=HEADERS
    )

    logger.info(f"Bank account link response: {response.json()}")
    return response.json()["url"]


def create_stripe_transfer_from_commission(user: User, commission: Commission):
    url = "https://api.stripe.com/v2/money_management/outbound_payments"

    amount = commission.money_amount * 100
    data = {
        "from": {
            "financial_account": STRIPE_FINANCIAL_ACCOUNT,
            "currency": STRIPE_FINANCIAL_ACCOUNT_CURRENCY
        },
        "to": {
            "recipient": user.stripe_account_id
        },
        "amount": {
            "value": amount,
            "currency": user.currency
        },
        "description": "Ambassador Payouts"
    }

    response = requests.post(
        url=url,
        json=data,
        headers=HEADERS
    )
    logger.info(f"Stripe transfer for commission {commission.id} response: {response.json()}")
    return response.json()

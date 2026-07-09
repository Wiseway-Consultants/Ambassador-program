from log.logger_config import logger

import requests
import stripe
from django.conf import settings

from commission.models import Commission
from prospect.utils import get_country_code_by_currency
from user.models import User

STRIPE_SECRET_KEY = settings.STRIPE_SECRET_KEY
stripe.api_key = STRIPE_SECRET_KEY

STRIPE_FINANCIAL_ACCOUNT = settings.STRIPE_FINANCIAL_ACCOUNT
STRIPE_FINANCIAL_ACCOUNT_CURRENCY = settings.STRIPE_FINANCIAL_ACCOUNT_CURRENCY
STRIPE_ACCOUNT_ID = settings.STRIPE_ACCOUNT_ID

HEADERS = {
    "Stripe-Version": "2026-05-27.preview",
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


def create_bank_account_onboarding_link(recipient_id: str):
    url = "https://api.stripe.com/v2/core/account_links"

    data = {
        "account": recipient_id,
        "use_case": {
            "type": "account_onboarding",
            "account_onboarding": {
                "configurations": [
                    "recipient"
                ],
                "return_url": "https://savefryoil.com/ambassador-referrals/stripe-profile/",
                "refresh_url": "https://savefryoil.com/ambassador-referrals/stripe-profile/"
            }
        }
    }

    response = requests.post(
        url,
        json=data,
        headers=HEADERS
    )

    logger.info(f"Bank account onboard link response: {response.json()}")
    return response.json()["url"]


def create_bank_account_update_link(recipient_id: str):
    url = "https://api.stripe.com/v2/core/account_links"

    data = {
        "account": recipient_id,
        "use_case": {
            "type": "account_update",
            "account_update": {
                "configurations": [
                    "recipient"
                ],
                "return_url": "https://savefryoil.com/ambassador-referrals/stripe-profile/",
                "refresh_url": "https://savefryoil.com/ambassador-referrals/stripe-profile/"
            }
        }
    }

    response = requests.post(
        url,
        json=data,
        headers=HEADERS
    )

    logger.info(f"Bank account update link response: {response.json()}")
    return response.json()["url"]


def create_stripe_outbound_payment_quote(user: User, commission: Commission, amount_value: int):
    """
    Creates an OutboundPaymentQuote, required for cross-border payments
    (e.g. GBP financial account -> USD payout method).
    """
    url = "https://api.stripe.com/v2/money_management/outbound_payment_quotes"

    data = {
        "from": {
            "financial_account": STRIPE_FINANCIAL_ACCOUNT,
            "currency": STRIPE_FINANCIAL_ACCOUNT_CURRENCY
        },
        "to": {
            "recipient": user.stripe_account_id,
            "currency": commission.currency
        },
        "amount": {
            "value": amount_value,
            "currency": commission.currency
        },
    }

    response = requests.post(
        url=url,
        json=data,
        headers={
            **HEADERS,
            "Stripe-Context": STRIPE_ACCOUNT_ID,
        }
    )
    response_data = response.json()
    logger.info(f"Stripe outbound payment quote response: {response_data}")

    if "error" in response_data:
        raise Exception(f"Failed to create outbound payment quote: {response_data['error']}")

    return response_data["id"]


def get_stripe_payout_method_for_currency(stripe_account_id: str, currency: str):
    url = "https://api.stripe.com/v2/money_management/payout_methods"
    response = requests.get(
        url,
        headers={
            **HEADERS,
            "Stripe-Context": stripe_account_id,
        }
    )
    methods = response.json().get("data", [])
    logger.info(f"Stripe payout methods for {stripe_account_id}: {methods}")

    for method in methods:
        supported = method.get("bank_account", {}).get("supported_currencies", [])
        if currency.lower() in supported:
            return method["id"]

    raise Exception(f"You are not ready to receive {currency} on your Stripe account {stripe_account_id}")


def create_stripe_transfer_from_commission(user: User, commission: Commission):
    url = "https://api.stripe.com/v2/money_management/outbound_payments"

    payout_method_id = get_stripe_payout_method_for_currency(user.stripe_account_id, commission.currency)
    amount_value = int(commission.money_amount * 100)

    logger.info(
        f"Attempting payout - recipient: {user.stripe_account_id}, payout_method: {payout_method_id}, currency: {commission.currency}, amount: {amount_value}"
    )
    # Cross-border payment (GBP -> foreign currency) requires a quote first
    quote_id = create_stripe_outbound_payment_quote(
        user=user,
        commission=commission,
        amount_value=amount_value,
    )

    data = {
        "from": {
            "financial_account": STRIPE_FINANCIAL_ACCOUNT,
            "currency": STRIPE_FINANCIAL_ACCOUNT_CURRENCY
        },
        "to": {
            "recipient": user.stripe_account_id,
            "payout_method": payout_method_id,
            "currency": commission.currency
        },
        "amount": {
            "value": amount_value,
            "currency": commission.currency
        },
        "description": f"Ambassador Payouts for commission {commission.prospect.restaurant_organisation_name}",
        "outbound_payment_quote": quote_id,
    }

    response = requests.post(
        url=url,
        json=data,
        headers={
            **HEADERS,
            "Stripe-Context": STRIPE_ACCOUNT_ID,
        }
    )
    response_data = response.json()
    logger.info(f"Stripe transfer for commission {commission.id} response: {response_data}")
    return response_data

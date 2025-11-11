from django.db import connection
from prospect.models import Prospect


def get_full_downline(user_id):
    query = """
    WITH RECURSIVE downline(level, user_id, prospect_id) AS (
        SELECT 1 AS level, u.id AS user_id, NULL AS prospect_id
        FROM user_user u
        WHERE u.invited_by_user_id = %s

        UNION ALL

        SELECT 1 AS level, NULL AS user_id, p.id AS prospect_id
        FROM prospect_prospect p
        WHERE p.invited_by_user_id = %s

        UNION ALL

        SELECT d.level + 1 AS level,
               COALESCE(u.id, d.user_id) AS user_id,
               COALESCE(p.id, d.prospect_id) AS prospect_id
        FROM downline d
        LEFT JOIN user_user u ON u.invited_by_user_id = d.user_id
        LEFT JOIN prospect_prospect p ON p.invited_by_user_id = d.user_id
        WHERE d.level < 7
    )
    SELECT prospect_id
    FROM downline
    WHERE prospect_id IS NOT NULL;
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [user_id, user_id])
        ids = [row[0] for row in cursor.fetchall()]
    return Prospect.objects.filter(id__in=ids).order_by('invited_by_user_id')


def get_country_code_by_currency(currency: str) -> str:
    currency = currency.upper()
    currency_to_country = {
        "GBP": "GB",
        "USD": "US",
        "EUR": "IE",
        "CAD": "CA",
        "AUD": "AU",
        "NZD": "NZ",
    }
    return currency_to_country[currency]


def get_currency_by_country_code(country_code: str) -> str:
    country_code = country_code.upper()
    country_to_currency = {
        "GB": "GBP",
        "UK": "GBP",
        "US": "USD",
        "IE": "EUR",
        "CA": "CAD",
        "AU": "AUD",
        "NZ": "NZD",
    }
    return country_to_currency.get(country_code, "")


def get_invitation_user_chain_from_prospect(prospect):
    """
    Returns a list of user IDs in the invitation chain for a given prospect.
    The order is: direct inviter first, then their inviter, and so on up the chain.
    """
    chain_ids = []
    user = prospect.invited_by_user

    while user or len(chain_ids) == 7:
        chain_ids.append(user)
        user = user.invited_by_user  # Move up the chain

    return chain_ids

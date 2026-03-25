from logging import getLogger
from os import getenv
import requests

from user.models import User

MAIL_CHIMP_API_KEY = getenv("MAIL_CHIMP_API_KEY")
logger = getLogger(__name__)

class MailChimpAPI:
    def __init__(self, api_key, dc, audience_id):
        self.api_key = api_key
        self.dc = dc
        self.audience_id = audience_id

    def add_contact_to_audience(
        self, user: User
    ):
        try:
            payload = {
                "language": "en",
                "email_channel": {
                    "email": user.email,
                    "marketing_consent": {"status": "confirmed"},
                },
                "merge_fields": {
                    "FNAME": user.first_name,
                    "LNAME": user.last_name,
                    "PHONE": user.phone
                },
            }
            req = requests.post(
                url=f"https://us11.api.mailchimp.com/3.0/audiences/{self.audience_id}/contacts",
                params={"merge_field_validation_mode": "strict", "data_mode": "live"},
                auth=("anystring", MAIL_CHIMP_API_KEY),
                json=payload,
            )
            logger.info(f"MailChimp response{req.json()}")
        except Exception as e:
            logger.error(f"MailChimp Error {str(e)}")



mailchimp_api = MailChimpAPI(api_key=MAIL_CHIMP_API_KEY, dc="us11", audience_id="3967e37352")

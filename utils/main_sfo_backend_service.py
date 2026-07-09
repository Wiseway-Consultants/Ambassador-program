from os import getenv

from dotenv import load_dotenv
import requests

from log.logger_config import logger

load_dotenv()

SFO_BACKEND_API_KEY = getenv("SFO_BACKEND_API_KEY")

class MainSfoBackendService:

    def __init__(self):
        self.base_url = "https://api.savefryoil.com"
        self.headers = {
            "x-api-key": SFO_BACKEND_API_KEY
        }

    def get_user_by_email(self, email):
        logger.info(f"Sending main api request to get user by email: {email}")
        response = requests.get(
            f"{self.base_url}/rm-dashboard/users?email={email}",
            headers=self.headers
        )
        data = response.json()
        if not data:
            return None
        return data[0]

sfo_backend_service = MainSfoBackendService()

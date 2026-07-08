import json
from log.logger_config import logger
from datetime import datetime, timedelta
from os import getenv
from pathlib import Path

import requests

CLIENT_ID = getenv("CLIENT_ID")
CLIENT_SECRET = getenv("CLIENT_SECRET")
SFO_BACKEND_API_KEY = getenv("SFO_BACKEND_API_KEY")



BASE_DIR = Path(__file__).resolve().parent.parent


class GoHighLevelAPI:
    def __init__(self):
        self.headers = {
            "Version": "2021-07-28",
            "Content-Type": "application/json",
            "Authorization": "Bearer ",
        }
        self.base_url = "https://services.leadconnectorhq.com"
        self.country_to_locationID = {
            "GB": "dNMN3zCANRj6BuScTLfC",
            "AU": "4Nh160QNZTSu12oiCecp",
            "CA": "tRAT9Du0M1EoncfpfJux",
            "IE": "rfqijwLULaFKIg2m0oP3",
            "NZ": "jQZrYYLodjByNxqCrehy",
            "US": "EhYpQQPMMPBIvrlubdE4"
        }

    @staticmethod
    def create_headers(access_token: str) -> dict:
        return {
            "Version": "2021-07-28",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

    @staticmethod
    def get_location_access_token(location_id):
        response = requests.post(
            url=f"https://api.savefryoil.com/ghl/token",
            headers={
                "x-api-key": SFO_BACKEND_API_KEY
            },
            json={
                "location_id": location_id,
            }
        )
        logger.info(f"Sent request to retrieve location token")
        return response.json()


    def create_contact(self, data, location_id):
        try:
            access_token = self.get_location_access_token(location_id)
            data["locationId"] = location_id
            request = requests.post(
                f"{self.base_url}/contacts",
                headers=self.create_headers(access_token),  # Create header with location access token
                json=data
            )
            response = request.json()

            if request.status_code != 201:
                logger.info(f"Error while creating contact\n{response}")
            else:
                logger.info(f"Contact created successfully\n{response}")
            return response
        except Exception as ex:
            logger.error(f"Error creating contact: {ex}")
            raise ex


GHL_API = GoHighLevelAPI()

import json
import logging
from datetime import datetime
from os import getenv
from pathlib import Path

import requests

CLIENT_ID = getenv("CLIENT_ID")
CLIENT_SECRET = getenv("CLIENT_SECRET")

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


class GoHighLevelAPI:
    def __init__(self):
        self.headers = {
            "Version": "2021-07-28",
            "Content-Type": "application/json",
            "Authorization": "Bearer ",
        }
        self.base_url = "https://services.leadconnectorhq.com"
        self.auth_file_path = Path(BASE_DIR, "auth", "ghl_jwt_auth.json")
        self.country_to_locationID = {
            "GB": "dNMN3zCANRj6BuScTLfC",
            "AU": "4Nh160QNZTSu12oiCecp",
            "CA": "tRAT9Du0M1EoncfpfJux",
            "IE": "rfqijwLULaFKIg2m0oP3",
            "NZ": "jQZrYYLodjByNxqCrehy",
            "US": "EhYpQQPMMPBIvrlubdE4"
        }

    def refresh_agency_token(self):
        try:
            logger.info("Refreshing agency token")
            with open(self.auth_file_path, "r") as file:
                tokens = json.load(file)
            response = requests.post(
                url=f"{self.base_url}/oauth/token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                data={
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": tokens["refresh_token"]
                }
            )
            if response.status_code == 200:
                with open(self.auth_file_path, "w") as file:
                    tokens["access_token"] = response.json()["access_token"]
                    tokens["expires_in"] = response.json()["expires_in"]
                    tokens["refresh_token"] = response.json()["refresh_token"]
                    tokens["refreshed_at"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
                    json.dump(tokens, file, indent=4)
                logger.info("AUTH TOKEN REFRESHED SUCCESSFULLY ^_^")
            else:
                logger.error(f"error [{response.status_code}]:\n {response.content}")

        except Exception as ex:
            logger.error('REFRESHER ERROR: ', ex)

    def get_location_access_token(self, country_code):
        with open(self.auth_file_path, "r") as file:
            tokens = json.load(file)
        agency_access_token = tokens["access_token"]
        location_id = self.country_to_locationID[country_code.upper()]
        response = requests.post(
            url=f"{self.base_url}/oauth/locationToken",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "Version": "2021-07-28",
                "Authorization": f"Bearer {agency_access_token}"
            },
            data={
                "locationId": location_id,
                "companyId": tokens["companyId"]
            }
        )
        return response.json()["access_token"]


GHL_API = GoHighLevelAPI()

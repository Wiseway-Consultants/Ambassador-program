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
        self.get_pipelineId_by_locationId = {
            "dNMN3zCANRj6BuScTLfC": "48oHU0QTQcxSoIl8cuBu",  # GB
            "4Nh160QNZTSu12oiCecp": "ZQBFmmJetqVtoDl3y73p",  # AU
            "tRAT9Du0M1EoncfpfJux": "pSpfLXy4c55vJJzc1431",  # CA
            "rfqijwLULaFKIg2m0oP3": "Z34If6HGBJc2J20jqbBz",  # IE
            "jQZrYYLodjByNxqCrehy": "ikwZZCZHHgT4pp3AVN5g",  # NZ
            "EhYpQQPMMPBIvrlubdE4": "zqaVu9yon8yO4QMyr81A",  # US
        }

    @staticmethod
    def create_headers(access_token: str) -> dict:
        return {
            "Version": "2021-07-28",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
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

    def get_location_access_token(self, location_id):
        with open(self.auth_file_path, "r") as file:
            tokens = json.load(file)
        agency_access_token = tokens["access_token"]
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

    def create_opportunity(self, data, location_id):
        try:
            access_token = self.get_location_access_token(location_id)
            pipeline_id = self.get_pipelineId_by_locationId[location_id]

            # Insert dynamic ids to request's body
            data["pipelineId"] = pipeline_id
            data["locationId"] = location_id

            request = requests.post(
                f"{self.base_url}/opportunities/",
                headers=self.create_headers(access_token),
                json=data
            )
            return request.json()
        except Exception as ex:
            logger.error(f"Error creating opportunity: {ex}")
            raise ex


GHL_API = GoHighLevelAPI()

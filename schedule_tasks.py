import time
from os import getenv

import requests
import schedule
from dotenv import load_dotenv

from utils.ghl_api import GHL_API

load_dotenv()
SERVER_TYPE = getenv("SERVER_TYPE")


def refresher():
    print("START REFRESHING PROCESS")
    GHL_API.refresh_agency_token()  # GHL access token


def cleanup_notifications():
    time.sleep(10)  # 10 seconds delay to wait server to start
    requests.get(
        f"http://{SERVER_TYPE}:8001/notifications/cleanup/",
        headers={
            "x-api-key": getenv("ADMIN_API_KEY")
        }
    )


print("Initialize schedule tasks")
refresher()
cleanup_notifications()
schedule.every(50).minutes.do(refresher)
schedule.every().day.do(cleanup_notifications)
# schedule.every(10).seconds.do(refresher)

while True:
    schedule.run_pending()
    time.sleep(1)

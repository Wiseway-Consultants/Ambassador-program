import os
import time
import schedule

from utils.ghl_api import GHL_API

cwd = os.getcwd()


def refresher():
    print("START REFRESHING PROCESS")
    GHL_API.refresh_agency_token()  # GHL access token


print("Initial refresh")
GHL_API.refresh_agency_token()
schedule.every(50).minutes.do(refresher)
# schedule.every(10).seconds.do(refresher)

while True:
    schedule.run_pending()
    time.sleep(1)

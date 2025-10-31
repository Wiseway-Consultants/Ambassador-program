from os import getenv

import requests
from dotenv import load_dotenv

TELEGRAM_TOKEN = getenv("TELEGRAM_NOTIFICATION_TOKEN")
TELEGRAM_CHAT_ID = getenv("TELEGRAM_NOTIFICATION_CHAT_ID")


def send_telegram_notification(message):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
    )

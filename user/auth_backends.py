from os import getenv

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from dotenv import load_dotenv
import hmac
import hashlib
import time

load_dotenv()
SALT_LOGIN_SECRET = getenv("SALT_LOGIN_SECRET")
TOKEN_MAX_AGE_SECONDS = 30

class EmailBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        user_model = get_user_model()
        try:
            email = kwargs.get('email', None)
            if email is None:
                email = kwargs.get('username', None)
            user = user_model.objects.get(email=email)
            if user.check_password(kwargs.get('password', None)):
                return user
        except user_model.DoesNotExist:
            return None
        return None


def verify_ambassador_login_salt(email: str, ts: str, token: str) -> bool:
    try:
        issued_at = int(ts)
    except ValueError:
        print("Invalid timestamp")
        return False

    if abs(time.time() - issued_at) > TOKEN_MAX_AGE_SECONDS:
        print("Token expired")
        return False  # expired or invalid date

    message = f"{email}:{ts}"
    print(f"Message: {message}")
    expected = hmac.new(
        SALT_LOGIN_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    print(f"Expected: {expected}")

    return hmac.compare_digest(expected, token)

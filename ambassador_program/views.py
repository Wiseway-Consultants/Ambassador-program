import logging
from os import path

from django.conf import settings
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.ghl_api import GHL_API
from utils.qr_code_tiger_api import qrTigerAPI

logger = logging.getLogger(__name__)


def openapi_yaml(request):
    filepath = path.join(settings.BASE_DIR, "staticfiles", "openapi.yaml")
    with open(filepath, "r") as f:
        return HttpResponse(f.read(), content_type="application/yaml")


def check_auth_key(headers):
    if "x-api-key" not in headers or headers["x-api-key"] != settings.ADMIN_API_KEY:
        raise PermissionError("Not Authorized")


class GHLview(APIView):
    def get(self, request):
        headers = request.headers
        try:
            check_auth_key(headers)
            GHL_API.refresh_agency_token()
            return Response("OK", status=200)
        except Exception as e:
            return Response(f"Error: {e}", status=400)

    def post(self, request):
        headers = request.headers
        try:
            check_auth_key(headers)
            data = request.data
            location_id = data["location_id"]
            location_access_token = GHL_API.get_location_access_token(location_id)
            return Response({"access_token": location_access_token}, status=200)

        except Exception as e:
            logger.error(f"Error with GHL admin token: {e}")
            return Response(f"Error: {e}", status=400)


class QRCodeView(APIView):

    def post(self, request):
        headers = request.headers
        try:
            check_auth_key(headers)

            data = request.data
            qr_url = data["qr_url"]
            qr_code_data = qrTigerAPI.create_static_qr_code(qr_url)
            return Response(qr_code_data, status=200)

        except Exception as e:
            return Response(f"Error: {e}", status=400)


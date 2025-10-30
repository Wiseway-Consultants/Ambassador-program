import os
import requests

from dotenv import load_dotenv


class QRCodeTigerAPI:
    def __init__(self):
        load_dotenv()
        self.BASE_URL = "https://api.qrtiger.com/api/"
        self.API_KEY = os.getenv("QR_CODE_TIGER_API_KEY")
        self.HEADERS = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.API_KEY}",
        }

    @staticmethod
    def prepare_dynamic_qr_code_payload(qr_url):
        data = {
            "qrType": "qr2",
            "qrCategory": "url",
            "qrUrl": qr_url,
            "qrName": "test",
            "qr": {
                "backgroundColor": None,
                "colorDark": "rgb(255,0,0)",
                "colorType": "SINGLE_COLOR",
                "eye_outer": "eyeOuter2",
                "eye_inner": "eyeInner1",
                "size": 500,
                "qrData": "pattern0",
                "transparentBkg": False,
                "logo": "https://media.qrtiger.com/images/2025/09/logo-(1)_82.png",
                "color01": "rgb(0,0,0)"
            }
        }
        return data

    @staticmethod
    def prepare_dynamic_qr_code_bundle_payload(qr_url, qr_frame_text):
        data = {
            "qrType": "qr2",
            "qrCategory": "url",
            "qrUrl": qr_url,
            "qrName": "test",
            "qr": {
                "color01": "rgb(250,190,20)",
                "logo": "https://media.qrtiger.com/images/2025/09/logo-(1)_82.png",
                "backgroundColor": "rgb(255,255,255)",
                "colorDark": "rgb(250,190,20)",
                "colorType": "SINGLE_COLOR",
                "grdType": "linear",
                "gradientType": "linear",
                "frame": 1,
                "frameColor": "rgb(12,86,165)",
                "frameColor2": "#3a74c5",
                "frameColorStyleType": "SINGLE_COLOR",
                "frameGradientType": "linear",
                "frameGradientStartColor": "#054080",
                "frameGradientEndColor": "rgb(243,5,5)",
                "frameText": qr_frame_text,
                "eye_outer": "eyeOuter2",
                "eye_inner": "eyeInner1",
                "eye_color": False,
                "size": 500,
                "qrData": "pattern0",
                "transparentBkg": False
            }
        }

        return data

    @staticmethod
    def prepare_static_qr_code_payload(qr_url):
        data = {
            "size": 500,
            "colorDark": "rgb(0,0,0)",
            "colorType": "SINGLE_COLOR",
            "logo": "https://media.qrtiger.com/images/2025/09/logo-(1)_82.png",
            "eye_outer": "eyeOuter2",
            "eye_inner": "eyeInner1",
            "qrData": "pattern0",
            "frameColor": "#054080",
            "frameColor2": "#3a74c5",
            "frameColorStyleType": "SINGLE_COLOR",
            "frameGradientType": "linear",
            "frameGradientStartColor": "#054080",
            "frameGradientEndColor": "#f30505",
            "frameText": "Scan me",
            "transparentBkg": False,
            "qrCategory": "url",
            "text": qr_url
        }
        return data

    def list_qr_codes(self, limit: int = 100):
        response = requests.get(
            self.BASE_URL + f"campaign/?limit={limit}",
            headers=self.HEADERS
        )
        return response.json()

    def get_qr_code_by_id(self, qr_id):
        response = requests.get(
            self.BASE_URL + f"data/{qr_id}",
            headers=self.HEADERS
        )
        return response.json()

    def create_qr_code(self, url):
        response = requests.post(
            self.BASE_URL + "campaign/",
            headers=self.HEADERS,
            json=self.prepare_dynamic_qr_code_payload(url)
        )
        return response.json()["qrId"]

    def create_qr_code_bundle(self, url, qr_frame_text):
        response = requests.post(
            self.BASE_URL + "campaign/",
            headers=self.HEADERS,
            json=self.prepare_dynamic_qr_code_bundle_payload(url, qr_frame_text)
        )
        return response.json()["qrId"]

    def create_static_qr_code(self, url):
        response = requests.post(
            self.BASE_URL + "qr/static",
            headers=self.HEADERS,
            json=self.prepare_static_qr_code_payload(url)
        )
        return response.json()

    def update_qr_code(self, qr_id, qr_name):
        response = requests.post(
            self.BASE_URL + f"campaign/edit/{qr_id}/",
            headers=self.HEADERS,
            json={"qrName": qr_name},
        )
        return response.json()["data"]["id"]

    def move_qr_code_to_folder(self, qr_id, folder_id: str = "68cadd04644bfd9d85a5f29b"):
        requests.post(
            f"https://qrtiger.com/folder/move/{folder_id}",
            headers=self.HEADERS,
            json={"qrIds": [qr_id]},
        )

    def create_qr_code_with_name(self, qr_url, qr_name):
        qr_code_campaign_id = self.create_qr_code(qr_url)
        qr_code_id = self.update_qr_code(qr_code_campaign_id, qr_name)
        self.move_qr_code_to_folder(qr_code_id)
        return qr_code_campaign_id

    def create_bundle_qr_code_with_name(self, qr_url, qr_frame_text, qr_name):
        qr_code_campaign_id = self.create_qr_code_bundle(qr_url, qr_frame_text)
        qr_code_id = self.update_qr_code(qr_code_campaign_id, qr_name)
        self.move_qr_code_to_folder(qr_code_id)
        return qr_code_campaign_id


qrTigerAPI = QRCodeTigerAPI()

import logging

from django.contrib.auth import get_user_model, update_session_auth_hash
from django.db import transaction
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings

from prospect.permissions import IsStaffUser
from utils.qr_code_tiger_api import qrTigerAPI
from .serializers import UserSerializer, TokenObtainPairSerializer, ChangePasswordSerializer
from utils.send_email import send_email

User = get_user_model()
signer = TimestampSigner()

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):

        logger.info(f"Received Registration request with payload: {request.data}")

        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"serializer error {serializer.errors}")
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            validated_data = serializer.validated_data
            password = validated_data.pop("password", None)
            user = User.objects.create_user(
                **validated_data,
                password=password,
                is_active=False
            )

            token = signer.sign(user.email)
            confirm_url = f"{settings.FRONTEND_URL}/confirm-email/?token={token}"

            send_email(user, confirm_url, "confirm")

        return Response(
            {"detail": "Account created. Please check your email to confirm registration."},
            status=status.HTTP_201_CREATED
        )


class ConfirmEmailView(APIView):
    permission_classes = []  # allow public access

    def post(self, request, *args, **kwargs):
        token = request.data.get("token")
        password = request.data.get("password")
        if not token or not password:
            return render(request, "email_verified.html", {"error": "Missing token or password."})

        try:
            email = signer.unsign(token, max_age=60 * 60 * 24)
            user = User.objects.get(email=email)

            if user.is_active:  # Check if user already active
                return Response({"detail": "Account already activated."}, status=200)

            user.set_password(password)
            user.is_active = True
            user.save()

            is_password_set = user.has_usable_password()
            return render(request, "email_verified.html", {"password_set": is_password_set})
        except SignatureExpired:  # render resend button if token expired
            return render(
                request,
                "email_verified.html",
                {
                    "error": "Your confirmation link has expired.",
                    "resend": True,
                    "email": signer.unsign(token, max_age=None)
                },
            )
        except (BadSignature, User.DoesNotExist):
            return render(request, "email_verified.html", {"error": "Invalid or broken confirmation link."})

    def get(self, request, *args, **kwargs):
        token = request.query_params.get("token")
        try:
            email = signer.unsign(token, max_age=60 * 60 * 24)
            user = User.objects.get(email=email)

            if user.is_active:  # Check if user already active
                return Response({"detail": "Account already activated."}, status=200)

            if not user.has_usable_password():
                #  User don't have password, render create password html
                return render(request, "email_verified.html", {"token": token})

            user.is_active = True
            user.save()
            return render(request, "email_verified.html", {"password_set": True})
        except SignatureExpired:  # render resend button if token expired
            return render(
                request,
                "email_verified.html",
                {
                    "error": "Your confirmation link has expired.",
                    "resend": True,
                    "email": signer.unsign(token, max_age=None)
                },
            )
        except (BadSignature, User.DoesNotExist):
            return render(request, "email_verified.html", {"error": "Invalid or broken confirmation link."})


class ResendConfirmationView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return render(request, "resend_success.html", {"error": "Account already activated."})

            token = signer.sign(user.email)
            confirm_url = f"{settings.FRONTEND_URL}/confirm-email/?token={token}"

            send_email(user, confirm_url, "confirm")

            return render(request, "resend_success.html")
        except User.DoesNotExist:
            return render(request, "resend_success.html", {"error": "Such User doesn't exist"})


class SendResetPasswordView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            email = request.data.get("email")
            user = User.objects.get(email=email)

            token = signer.sign(user.email)  # signed token, expirable
            reset_url = f"{settings.FRONTEND_URL}/reset-password/?token={token}"

            send_email(user, reset_url, "reset")

            return Response(
                {"detail": "Reset Email sent to user"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Such User doesn't exist"},
                status=status.HTTP_404_NOT_FOUND
            )


class ResetPasswordView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        token = request.query_params.get("token")
        try:
            email = signer.unsign(token, max_age=60 * 60)  # 1h validity
            return render(request, "reset_password.html", {"token": token})
        except SignatureExpired:
            return render(request, "reset_password.html", {"error": "This reset link has expired."})
        except BadSignature:
            return render(request, "reset_password.html", {"error": "Invalid reset link."})

    def post(self, request, *args, **kwargs):
        token = request.data.get("token")
        password = request.data.get("password")

        try:
            email = signer.unsign(token, max_age=60 * 60)
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
            return render(request, "reset_password_success.html")
        except (SignatureExpired, BadSignature, User.DoesNotExist):
            return render(request, "reset_password.html", {"error": "Invalid or expired reset link."})


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            if not user.check_password(serializer.validated_data["old_password"]):
                return Response({"old_password": "Wrong password"}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data["new_password"])
            user.save()

            # Keep user logged in after password change
            update_session_auth_hash(request, user)

            return Response({"detail": "Password updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QrCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        try:

            qr_url = f"https://savefryoil.com/ambassador-referrals/?referral_code={user.referral_code}"
            qr_name = f"ambassador_{user.email}"
            qr_id = qrTigerAPI.create_qr_code_with_name(qr_url, qr_name)
            user.referral_qr_code_id = qr_id
            user.save()
            return Response({"detail": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        user = request.user

        qr_id = user.referral_qr_code_id
        if not qr_id:
            return Response({"error": "No QR code found."}, status=status.HTTP_400_BAD_REQUEST)
        qr_code_data = qrTigerAPI.get_qr_code_by_id(qr_id)
        return Response(qr_code_data, status=status.HTTP_200_OK)


class StaffQrCodeView(APIView):
    permission_classes = [IsStaffUser,]

    def post(self, request):
        user = request.user

        try:
            data = request.data
            code_bundle_type = data["code_bundle_type"]
            if code_bundle_type not in ["Industry", "Affinity", "B2B"]:
                return Response({"error": "code_bundle_type is not valid."}, status=status.HTTP_400_BAD_REQUEST)

            qr_url = None
            qr_frame_text = None
            if code_bundle_type == "Industry":
                qr_url = (f"https://savefryoil.retool.com/embedded/public/98912f22-4534-4209-af8e-d6d4e16dc706"
                          f"?referral_code={user.referral_code}")
                qr_frame_text = "Industry"
            if code_bundle_type == "Affinity":
                qr_url = "https://savefryoil.retool.com/embedded/public/6330dac3-e5e7-428e-b675-66cf44e65c61"
                qr_frame_text = "Affinity"
            if code_bundle_type == "B2B":
                qr_url = "https://savefryoil.retool.com/embedded/public/e556ad0c-c4c0-4eaa-8f5d-b49753bc4f8a"
                qr_frame_text = "B2B"

            qr_name = f"Code Bundle {user.email}"

            qr_id = qrTigerAPI.create_bundle_qr_code_with_name(qr_url, qr_frame_text, qr_name)
            bundle_dict = user.qr_code_bundles
            bundle_dict[code_bundle_type] = qr_id
            user.qr_code_bundles = bundle_dict
            user.save()
            return Response({"detail": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        user = request.user

        qr_code_bundles_id = user.qr_code_bundles
        if not qr_code_bundles_id:
            return Response({"error": "No QR code bundles found."}, status=status.HTTP_400_BAD_REQUEST)

        qr_codes_data = {}
        for qr_name, qr_code_id in qr_code_bundles_id.items():
            qr_code_data = qrTigerAPI.get_qr_code_by_id(qr_code_id)
            qr_codes_data[qr_name] = qr_code_data

        return Response(qr_codes_data, status=status.HTTP_200_OK)


import logging
import requests
import jwt
from jwt.algorithms import RSAAlgorithm
import time

from django.contrib.auth import get_user_model, update_session_auth_hash
from django.db import transaction
from django.db.models import F
from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from notifications.utils import send_notification
from prospect.permissions import IsStaffUser, IsSuperUser
from utils.qr_code_tiger_api import qrTigerAPI
from utils.send_telegram_notification import send_telegram_notification
from .serializers import UserSerializer, TokenObtainPairSerializer, ChangePasswordSerializer, AdminUserSerializer
from utils.send_email import send_email

User = get_user_model()
signer = TimestampSigner()

logger = logging.getLogger(__name__)


class GoogleLoginView(APIView):
    """
    Google OAuth login - returns JWT tokens directly
    """
    http_method_names = ["post"]

    def post(self, request):
        logger.info(f"Google sign in/up data: {request.data}")
        google_id_token = request.data.get('id_token')
        client_id = request.data.get('client_id')

        if not google_id_token or not client_id:
            logger.error("Request body missing a google id_token or client_id")
            return Response(
                {'error': 'Google id_token and client_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:

            # Verify Google ID token
            logger.info("Start google's token verification")
            id_info = id_token.verify_oauth2_token(
                google_id_token,
                google_requests.Request(),
                client_id
            )

            email = id_info.get('email')
            email_verified = id_info.get('email_verified', False)
            first_name = id_info.get('given_name', '')
            last_name = id_info.get('family_name', '')

            if not email_verified:
                logger.error("Email verification failed")
                return Response(
                    {'error': 'Email not verified by Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                # Get or create user
                logger.info("Start get or create user")
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': True,
                    }
                )

                if created:
                    logger.info(f"User is created with id: {user.id}")
                    user.set_unusable_password()
                    user.save()
                else:
                    logger.info(f"User already registered")
                    # Activate if not active
                    if not user.is_active:
                        user.is_active = True
                        user.save()

                # Generate JWT tokens - SAME AS EMAIL/PASSWORD LOGIN
                logger.info("Generate JWT token")
                refresh = RefreshToken.for_user(user)
                logger.info("JWT token generated successfully")

                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Google OAuth error: {str(e)}")
            return Response(
                {'error': 'Authentication failed'},
                status=status.HTTP_400_BAD_REQUEST
            )


class AppleSignInView(APIView):
    permission_classes = []

    def post(self, request):
        logger.info(f"Payload: {request.data}")
        identity_token = request.data.get('identity_token')
        user_id = request.data.get('user_id')
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not identity_token:
            return Response(
                {'error': 'identity_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the identity token
        try:
            decoded_token = self.verify_apple_token(identity_token)
        except Exception as e:
            return Response(
                {'error': f'Invalid token: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Extract user info from token
        apple_user_id = decoded_token.get('sub')
        token_email = decoded_token.get('email')
        logger.info(f"token_email: {token_email}")

        # Use email from token if available, otherwise from request
        user_email = token_email or email

        # Get or create user
        user, created = User.objects.get_or_create(
            apple_user_id=apple_user_id,
            defaults={
                'is_active': True
            }
        )

        # Update name only if user was just created and names were provided
        if created and (first_name or last_name or user_email):
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if user_email:
                user.email = user_email
            user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'is_new_user': created,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_200_OK)

    def verify_apple_token(self, identity_token):
        """
        Verify Apple's identity token
        """
        # Get Apple's public keys
        apple_keys_url = 'https://appleid.apple.com/auth/keys'
        response = requests.get(apple_keys_url)
        apple_keys = response.json()
        logger.info(f"Apple keys: {apple_keys}")

        # Decode token header to get the key id (kid)
        header = jwt.get_unverified_header(identity_token)
        logger.info(f"header from identity token: {header}")
        kid = header.get('kid')

        # Find the matching public key
        public_key = None
        for key in apple_keys['keys']:
            if key['kid'] == kid:
                public_key = RSAAlgorithm.from_jwk(key)
                break

        logger.info(f"Public key: {public_key}")
        if not public_key:
            raise ValueError('Unable to find matching public key')

        # Verify and decode the token
        decoded = jwt.decode(
            identity_token,
            public_key,
            algorithms=['RS256'],
            audience='com.savefryoil.ambassador',  # Replace with your iOS app bundle ID
            issuer='https://appleid.apple.com'
        )
        logger.info(f"decoded JWT: {decoded}")

        # Verify expiration
        if decoded.get('exp', 0) < time.time():
            raise ValueError('Token has expired')

        return decoded


class RegisterView(APIView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):

        logger.info(f"Received Registration request with payload: {request.data}")

        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"serializer error {serializer.errors}")
            send_telegram_notification(f"Error Ambassador Registration {serializer.errors}")
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
        logger.info(f"Received Confirm Email request with payload: {request.data}")
        token = request.data.get("token")
        password = request.data.get("password")
        if not token or not password:
            logger.error(f"Token and password missing in email confirmation request")
            return render(request, "email_verified.html", {"error": "Missing token or password."})

        try:
            email = signer.unsign(token, max_age=60 * 60 * 48)
            user = User.objects.get(email=email)

            if user.is_active:  # Check if user already active
                logger.error(f"Account is already active")
                return Response({"detail": "Account already activated."}, status=200)

            user.set_password(password)
            user.is_active = True
            user.save()

            is_password_set = user.has_usable_password()
            logger.info(f"Password is successfully set")
            return render(request, "email_verified.html", {"password_set": is_password_set})
        except SignatureExpired:  # render resend button if token expired
            logger.error(f"Signature Expired")
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
            logger.error(f"Bad signature or user does not exist")
            return render(request, "email_verified.html", {"error": "Invalid or broken confirmation link."})

    def get(self, request, *args, **kwargs):
        token = request.query_params.get("token")
        try:
            email = signer.unsign(token, max_age=60 * 60 * 48)
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
        logger.info(f"Received request to update user profile {request.user.email}, data: {request.data}")
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            send_notification(
                request.user.id,
                "You successfully updated your profile",
                "success",
                "Profile Updated"
            )
            logger.info(f"Profile updated successfully")
            return Response(serializer.data)
        logger.error(f"Error, user was not updated: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        logger.info(f"Received request to change {request.user.email} password")
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            if user.has_usable_password():
                if not user.check_password(serializer.validated_data["old_password"]):
                    logger.error(f"Wrong old password input")
                    return Response({"old_password": "Wrong password"}, status=status.HTTP_400_BAD_REQUEST)

            else:
                logger.info("Skipping old password check because user has no usable password")
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            # Keep user logged in after password change
            update_session_auth_hash(request, user)
            send_notification(
                request.user.id,
                "You successfully changed your password",
                "success",
                "Password Changed"
            )

            logger.info("Password changed successfully")
            return Response({"detail": "Password updated successfully"}, status=status.HTTP_200_OK)

        logger.error(f"Password wasn't changed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        logger.info(f"Received request to delete: {user.email} with id - {user.id}")
        try:
            user.is_active = False
            logger.info("User 'deleted'(set to inactive) successfully")
            return Response({"detail": "User deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error deleting user with id {user.id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StaffAmbassadorView(ListAPIView):
    permission_classes = [IsStaffUser]
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(invited_by_user=user)
        return queryset


class AdminAmbassadorView(ListAPIView):
    permission_classes = [IsSuperUser]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        return (
            User.objects
            .all()
            .annotate(
                is_invited_by_rm=F("invited_by_user__is_staff")
            )
        )


class QrCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        try:
            logger.info("Received request to generate ambassador referral QR code")
            qr_url = f"https://savefryoil.com/ambassador-referrals/?referral_code={user.referral_code}"
            qr_name = f"ambassador_{user.email}"
            qr_id = qrTigerAPI.create_qr_code_with_name(qr_url, qr_name)
            user.referral_qr_code_id = qr_id
            user.save()
            send_notification(
                request.user.id,
                "Ambassador QR Code generated successfully",
                "success",
                "QR Code Generated"
            )

            logger.info(f"Ambassador QR Code generated successfully with qr id: {qr_id}")
            return Response({"detail": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error generating ambassador QR code: {e}")
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
            logger.info(f"Received request to generate Staff QR code Bundle {data}")

            code_bundle_type = data["code_bundle_type"]
            if code_bundle_type not in ["Industry", "Affinity", "B2B"]:
                logger.error(f"Wrong code bundle type: {code_bundle_type}")
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
            logger.info("Successfully generated Staff QR code")
            return Response({"detail": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error generating Staff QR code: {e}")
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


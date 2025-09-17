from django.contrib.auth import get_user_model, update_session_auth_hash
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from django.conf import settings

from .serializers import UserSerializer, TokenObtainPairSerializer, ChangePasswordSerializer

User = get_user_model()
signer = TimestampSigner()


class RegisterView(APIView):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # Create user as inactive until email is confirmed

            validated_data = serializer.validated_data
            password = validated_data.pop("password", None)

            if password:
                user = User.objects.create_user(
                    **serializer.validated_data,
                    password=password,
                    is_active=False
                )

            else:
                user = User.objects.create_user(
                    **serializer.validated_data,
                    is_active=False
                )
                user.set_unusable_password()
                user.save()

            # Generate confirmation token
            token = signer.sign(user.email)
            confirm_url = f"{settings.FRONTEND_URL}/confirm-email/?token={token}"

            # Send confirmation email
            send_mail(
                subject="Confirm your SaveFryOil Ambassador account",
                message=f"Hi {user.first_name},\n\nPlease confirm your account by clicking the link below:\n\n{confirm_url}\n\nIf you didn’t register, just ignore this email.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

            return Response(
                {"detail": "Account created. Please check your email to confirm registration."},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class ResendConfirmationView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return render(request, "resend_success.html", {"error": "Account already activated."})

            # generate new token
            token = signer.sign(user.email)
            confirm_url = f"{settings.FRONTEND_URL}/confirm-email/?token={token}"

            send_mail(
                subject="Confirm your SaveFryOil Ambassador account",
                message=f"Hi {user.first_name},\n\nPlease confirm your account by clicking the link below:\n\n{confirm_url}\n\nIf you didn’t register, ignore this email.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

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

            send_mail(
                subject="Reset your password",
                message=f"Hi {user.first_name},\n\nClick the link below to reset your password:\n\n{reset_url}\n\nIf you didn’t request this, ignore this email.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
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


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=False)
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

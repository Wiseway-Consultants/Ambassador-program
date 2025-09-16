from django.contrib.auth import get_user_model, update_session_auth_hash
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
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

            user = User.objects.create_user(
                **serializer.validated_data,
                is_active=False
            )

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
                status=HTTP_201_CREATED
            )

        return Response(
            {"errors": serializer.errors},
            status=HTTP_400_BAD_REQUEST
        )


class ConfirmEmailView(APIView):
    permission_classes = []  # allow public access

    def get(self, request, *args, **kwargs):
        token = request.query_params.get("token")
        try:
            email = signer.unsign(token, max_age=60*60*24)  # 24h validity
            user = User.objects.get(email=email)
            user.is_active = True
            user.save()
            return render(request, "email_verified.html")  # ✅ success
        except SignatureExpired:
            return render(request, "email_verified.html", {"error": "Your confirmation link has expired."})
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

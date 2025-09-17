from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import EmailTokenObtainPairView, RegisterView, ProfileView, ConfirmEmailView, ResendConfirmationView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='token_obtain_pair'),
    path("auth/confirm-email/", ConfirmEmailView.as_view(), name="confirm-email"),
    path("auth/resend-confirmation/", ResendConfirmationView.as_view(), name="confirm-email"),
    path('token/obtain/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("profile/", ProfileView.as_view(), name="profile"),
]

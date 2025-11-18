from django.urls import path
from user.stripe_profile_views import (
    StripeProfileView,
    StripeOnboardingEmailView
)

urlpatterns = [
    path('profile/', StripeProfileView.as_view(), name='stripe'),
    path('onboard/', StripeOnboardingEmailView.as_view(), name='stripe_onboard'),
]

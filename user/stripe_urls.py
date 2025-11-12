from django.urls import path

from user.stripe_profile_views import (
    StripeProfileView,
    StripeOnboardingView,
    StripeAccountView,
    StripePayoutsView
)

urlpatterns = [
    path('profile/', StripeProfileView.as_view(), name='stripe-profile'),
    path('profile/payouts/', StripePayoutsView.as_view(), name='stripe-payouts'),
    path('profile/login-link/', StripeAccountView.as_view(), name='stripe-login-link'),
    path('onboarding/send/', StripeOnboardingView.as_view(), name='stripe-onboarding'),
]

from django.urls import path
from user.stripe_profile_views import (
    StripeProfileView,
    StripeOnboardingEmailView, StripePayoutsView
)

urlpatterns = [
    path('profile/', StripeProfileView.as_view(), name='stripe'),
    path('onboard/', StripeOnboardingEmailView.as_view(), name='stripe_onboard'),
    path('payout/', StripePayoutsView.as_view(), name='stripe_payouts'),
]

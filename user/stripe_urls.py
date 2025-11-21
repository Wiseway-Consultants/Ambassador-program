from django.urls import path
from user.stripe_profile_views import (
    StripeProfileView,
    StripeOnboardingEmailView,
    StripePayoutsView,
    StripeAccountUpdateEmailView
)

urlpatterns = [
    path('profile/', StripeProfileView.as_view(), name='stripe'),
    path('onboard/', StripeOnboardingEmailView.as_view(), name='stripe_onboard'),
    path('account_update/', StripeAccountUpdateEmailView.as_view(), name='stripe_account_update'),
    path('payout/', StripePayoutsView.as_view(), name='stripe_payouts'),
]

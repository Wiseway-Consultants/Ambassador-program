from django.urls import path

from user.stripe_profile_views import StripeProfileView, StripeOnboardingView

urlpatterns = [
    path('profile/', StripeProfileView.as_view(), name='stripe-profile'),
    path('onboarding/send/', StripeOnboardingView.as_view(), name='stripe-onboarding'),
]

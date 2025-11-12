from django.urls import path

from user.stripe_profile_views import StripeProfileView

urlpatterns = [
    path('', StripeProfileView.as_view(), name='stripe-profile'),
]

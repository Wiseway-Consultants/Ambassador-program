from django.urls import path

from commission.views import (
    CommissionClaimView,
    CommissionListView,
    StripeRecipientView,
    CommissionPaidView,
)

urlpatterns = [
    path('recipients/', StripeRecipientView.as_view(), name='stripe-recipients'),
    path('claim/', CommissionClaimView.as_view(), name='claim-commission'),
    path('paid/', CommissionPaidView.as_view(), name='paid-commission'),
    path('', CommissionListView.as_view(), name='commission-list'),
]

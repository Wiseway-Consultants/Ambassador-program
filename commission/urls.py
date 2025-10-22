from django.urls import path

from commission.views import CommissionClaimView

urlpatterns = [
    path('claim/', CommissionClaimView.as_view(), name='claim-commission'),
]

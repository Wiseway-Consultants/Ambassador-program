from django.urls import path

from commission.views import CommissionClaimView, CommissionListView

urlpatterns = [
    path('claim/', CommissionClaimView.as_view(), name='claim-commission'),
    path('', CommissionListView.as_view(), name='commission-list'),
]

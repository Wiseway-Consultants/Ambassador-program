from django.urls import path

from prospect.views import ProspectView, StaffProspectViewSet, CompleteDealView, GhlWebhookView

urlpatterns = [
    path('', ProspectView.as_view(), name='prospect'),
    path('ghl/webhook/', GhlWebhookView.as_view(), name='ghl-webhook-handler'),
    path('deal/complete/', CompleteDealView.as_view(), name='prospect-complete-deal'),
    path('sales/', StaffProspectViewSet.as_view({'get': 'list', 'post': 'create'}), name='prospect-sales'),
]

from django.urls import path

from prospect.views import ProspectView, StaffProspectViewSet

urlpatterns = [
    path('', ProspectView.as_view(), name='prospect'),
    path('sales/', StaffProspectViewSet.as_view({'get': 'list', 'post': 'create'}), name='prospect-sales'),
]

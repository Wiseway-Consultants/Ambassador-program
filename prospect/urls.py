from django.urls import path

from prospect.views import ProspectView

urlpatterns = [
    path('', ProspectView.as_view(), name='prospect'),
]

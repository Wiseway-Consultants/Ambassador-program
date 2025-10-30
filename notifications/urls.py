from django.urls import path

from notifications.views import NotificationView

urlpatterns = [
    path('', NotificationView.as_view(), name='retrieve-notifications'),
]

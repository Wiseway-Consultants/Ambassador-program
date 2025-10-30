from django.urls import path

from notifications.views import NotificationView, NotificationCleanUpView

urlpatterns = [
    path('', NotificationView.as_view(), name='retrieve-notifications'),
    path('cleanup/', NotificationCleanUpView.as_view(), name='notifications-cleanup'),
]

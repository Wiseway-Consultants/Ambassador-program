from django.urls import path

from notifications.views import NotificationView, NotificationCleanUpView, PushNotificationDeviceView

urlpatterns = [
    path('', NotificationView.as_view(), name='retrieve-notifications'),
    path('register-device/', PushNotificationDeviceView.as_view(), name='fcm-token'),
    path('cleanup/', NotificationCleanUpView.as_view(), name='notifications-cleanup'),
]

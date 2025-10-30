import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from ambassador_program.views import check_auth_key

logger = logging.getLogger(__name__)


class NotificationView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(user=user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        notifications = Notification.objects.filter(user=user, read=False).update(read=True)

        return Response({"notifications_updated": notifications})

    def patch(self, request):
        user = request.user
        url_params = request.query_params
        notification_id = url_params.get("notification_id")
        notification = Notification.objects.filter(user=user, read=False, id=notification_id).update(read=True)

        return Response({"notification_updated": notification})


class NotificationCleanUpView(APIView):

    def get(self, request):
        headers = request.headers
        try:
            check_auth_key(headers)
            logger.info("🧹 Starting cleanup of old read notifications...")
            cutoff_date = timezone.now() - timedelta(weeks=2)
            deleted_count, _ = Notification.objects.filter(
                read=True, created_at__lt=cutoff_date
            ).delete()
            logger.info(f"🧹 Deleted {deleted_count} old notifications.")
            return Response({"detail": f"Successfully deleted {deleted_count} old notifications"}, status=200)
        except Exception as e:
            return Response(f"Error: {e}", status=400)

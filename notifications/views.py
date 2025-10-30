from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.serializers import NotificationSerializer


class NotificationView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        notifications = user.notifications.filter(user=user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        notifications = user.notifications.filter(user=user, read=False).update(read=True)

        return Response({"notifications_updated": notifications})

    def patch(self, request):
        user = request.user
        url_params = request.query_params
        notification_id = url_params.get("notification_id")
        notification = user.notifications.filter(user=user, read=False, id=notification_id).update(read=True)

        return Response({"notification_updated": notification})

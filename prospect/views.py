from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from prospect.models import Prospect
from prospect.permissions import IsStaffUser
from prospect.serializers import ProspectSerializer
from prospect.utils import get_full_downline


class ProspectView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_set = get_full_downline(request.user.id)
        serializer = ProspectSerializer(query_set, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a prospect either by a User (default)
        or by another Prospect (if `invited_by_prospect_id` is provided).
        """
        serializer = ProspectSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            phone = serializer.validated_data["phone"]

            # Prevent duplicates
            if Prospect.objects.filter(Q(email=email) | Q(phone=phone)).first():
                return Response(
                    {"detail": "Prospect with this email or phone already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Default case: invited by authenticated user
            prospect = serializer.save(invited_by_user=request.user)

            return Response(
                ProspectSerializer(prospect).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffProspectViewSet(ModelViewSet):
    queryset = Prospect.objects.all().order_by('-id')
    serializer_class = ProspectSerializer
    permission_classes = [IsStaffUser]

    def create(self, request, *args, **kwargs):  # Overwrite POST method
        data = request.data

        return Response(data, status=status.HTTP_201_CREATED)



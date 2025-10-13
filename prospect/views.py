from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from prospect.models import Prospect
from prospect.permissions import IsStaffUser
from prospect.serializers import ProspectSerializer
from prospect.utils import get_full_downline, get_country_code_by_currency
from utils.ghl_api import GHL_API
from utils.prepare_payload import prospect_prepare_payload


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
    serializer_class = ProspectSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):  # return different queryset if user is not superuser
        user = self.request.user
        if user.is_superuser:
            return Prospect.objects.all().order_by('-id')

        user_country = get_country_code_by_currency(user.currency)
        return Prospect.objects.all().filter(country__iexact=user_country).order_by('-id')

    def create(self, request, *args, **kwargs):  # Overwrite POST method
        data = request.data

        ghl_contacts_id = []
        error_ghl_contacts = []
        ghl_opportunities_id = []

        try:
            for prospect in data["prospects"]:
                try:

                    # 1 Prepare GHL data
                    ghl_location_id = GHL_API.country_to_locationID[prospect["country"]]
                    contact_payload = prospect_prepare_payload.ghl_contact_create(prospect)

                    # 2 Create contact in GHL
                    contact = GHL_API.create_contact(contact_payload, ghl_location_id)
                    contact_id = contact.get("contact", {}).get("id")

                    if not contact_id:
                        error_ghl_contacts.append(prospect["email"])
                        continue

                    ghl_contacts_id.append(contact_id)

                    # 3 Create opportunity
                    opportunity_payload = prospect_prepare_payload.ghl_opportunity_create(prospect, contact_id)
                    opportunity = GHL_API.create_opportunity(opportunity_payload, location_id=ghl_location_id)
                    opportunity_id = opportunity.get("opportunity", {}).get("id")

                    ghl_opportunities_id.append(opportunity_id)

                    # 4 Update Prospect
                    db_prospect = Prospect.objects.get(id=prospect["id"])
                    db_prospect.ghl_contact_id = contact_id
                    db_prospect.ghl_opportunity_id = opportunity_id
                    db_prospect.save(update_fields=["ghl_contact_id", "ghl_opportunity_id"])

                except Exception as e:
                    error_ghl_contacts.append({"email": prospect["email"], "error": str(e)})

            return Response(
                {
                    "contacts_id": ghl_contacts_id,
                    "error_contacts": error_ghl_contacts,
                    "opportunities_id": ghl_opportunities_id,
                }, status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({
                "error": str(e),
                "successful_contacts": ghl_contacts_id,
                "successful_opportunities": ghl_opportunities_id,
            }, status=status.HTTP_400_BAD_REQUEST)


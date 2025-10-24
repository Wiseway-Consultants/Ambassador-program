import base64
import logging

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
from utils.ghl_api import GHL_API
from utils.prepare_payload import prospect_prepare_payload
from ambassador_program.views import check_auth_key

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

logger = logging.getLogger(__name__)


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

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Prospect.objects.all().order_by('-id')
        return Prospect.objects.none()

    def create(self, request, *args, **kwargs):  # Overwrite POST method. Submit to GHL logic
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
                    db_prospect.ghl_location_id = ghl_location_id
                    db_prospect.save(update_fields=["ghl_contact_id", "ghl_opportunity_id", "ghl_location_id"])

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


class CompleteDealView(APIView):

    def post(self, request):
        headers = request.headers
        try:
            check_auth_key(headers)
            data = request.data
            logger.info(f"Deal Completed in GHL: {data}")
            contact_id = data.get("contact_id")
            opportunity_id = data.get("id")

            prospect = Prospect.objects.get(ghl_contact_id=contact_id, ghl_opportunity_id=opportunity_id)
            prospect.deal_completed = True
            prospect.save(update_fields=["deal_completed"])
            return Response({"detail": "deal_completed"})
        except PermissionError as e:
            return Response({"error": str(e)}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class GhlWebhookView(APIView):

    def post(self, request, *args, **kwargs):
        # 1️⃣ Get raw body (byte-for-byte)
        raw_body = request.body  # important: don’t decode or parse yet

        # 2️⃣ Extract signature from headers
        signature_b64 = request.headers.get("x-wh-signature")
        if not signature_b64:
            return Response({"error": "Missing signature"}, status=400)

        try:
            signature_bytes = base64.b64decode(signature_b64)
        except Exception:
            return Response({"error": "Invalid signature format"}, status=400)

        # 3️⃣ Load GHL’s public key
        GHL_PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
        MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAokvo/r9tVgcfZ5DysOSC
        Frm602qYV0MaAiNnX9O8KxMbiyRKWeL9JpCpVpt4XHIcBOK4u3cLSqJGOLaPuXw6
        dO0t6Q/ZVdAV5Phz+ZtzPL16iCGeK9po6D6JHBpbi989mmzMryUnQJezlYJ3DVfB
        csedpinheNnyYeFXolrJvcsjDtfAeRx5ByHQmTnSdFUzuAnC9/GepgLT9SM4nCpv
        uxmZMxrJt5Rw+VUaQ9B8JSvbMPpez4peKaJPZHBbU3OdeCVx5klVXXZQGNHOs8gF
        3kvoV5rTnXV0IknLBXlcKKAQLZcY/Q9rG6Ifi9c+5vqlvHPCUJFT5XUGG5RKgOKU
        J062fRtN+rLYZUV+BjafxQauvC8wSWeYja63VSUruvmNj8xkx2zE/Juc+yjLjTXp
        IocmaiFeAO6fUtNjDeFVkhf5LNb59vECyrHD2SQIrhgXpO4Q3dVNA5rw576PwTzN
        h/AMfHKIjE4xQA1SZuYJmNnmVZLIZBlQAF9Ntd03rfadZ+yDiOXCCs9FkHibELhC
        HULgCsnuDJHcrGNd5/Ddm5hxGQ0ASitgHeMZ0kcIOwKDOzOU53lDza6/Y09T7sYJ
        PQe7z0cvj7aE4B+Ax1ZoZGPzpJlZtGXCsu9aTEGEnKzmsFqwcSsnw3JB31IGKAyk
        T1hhTiaCeIY/OwwwNUY2yvcCAwEAAQ==
        -----END PUBLIC KEY-----"""
        public_key = serialization.load_pem_public_key(GHL_PUBLIC_KEY)

        # 4️⃣ Verify signature
        try:
            public_key.verify(
                signature_bytes,
                raw_body,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            verified = True
        except InvalidSignature:
            verified = False

        if not verified:
            logger.warning("❌ Invalid GHL webhook signature.")
            return Response({"error": "Invalid signature"}, status=401)

        # 5️⃣ Parse JSON safely after verification
        payload = request.data
        event = payload.get("type")
        logger.info(f"✅ Valid GHL webhook received: {payload}")

        # 6️⃣ Handle different event types
        if event == "ContactDelete":
            contact_id = payload.get("id")
            location_id = payload.get("locationId")
            # e.g. mark contact as deleted in your DB
            prospect = Prospect.objects.get(ghl_contact_id=contact_id, ghl_location_id=location_id)
            prospect.ghl_contact_id = None
            prospect.ghl_opportunity_id = None
            prospect.ghl_location_id = None
            prospect.save(update_fields=["ghl_contact_id", "ghl_opportunity_id", "ghl_location_id"])
            logger.info(f"Delete prospect's: {prospect.email} GHL opportunity and contact id")

        # 7️⃣ Always return 200 quickly so GHL doesn’t retry
        return Response({"detail": "success"}, status=200)

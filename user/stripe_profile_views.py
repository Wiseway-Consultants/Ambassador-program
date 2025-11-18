import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import stripe

from commission.models import Commission
from commission.serializers import CommissionStripePayoutSerializer
from commission.utlis import create_stripe_express_account, create_stripe_transfer, retrieve_recipient_stripe
from prospect.permissions import IsSuperUser

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            user = request.user
            logger.info(f"Request to retrieve ambassador's stripe account: {user.email}")
            user_stripe_acc_id = user.stripe_account_id
            if not user_stripe_acc_id:
                logger.error(f"User doesn't have stripe account")
                return Response(
                    {
                        "error": "You doesn't have Recipient Stripe account"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            account = retrieve_recipient_stripe(user)
            payment_capability_status = account["configuration"]["recipient"]["capabilities"]["bank_accounts"]["local"]["status"]
            if user.stripe_onboard_status is False and payment_capability_status == "active":
                user.stripe_onboard_status = True
                user.save()
                logger.info(f"Stripe account {user_stripe_acc_id} is onboard")
            logger.debug(f"Stripe Account retrieved: {account}")
            return Response(account)
        except Exception as e:
            logger.error(f"Error getting stripe_profile: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StripePayoutsView(APIView):

    permission_classes = (IsSuperUser, )

    def post(self, request):

        data = request.data
        serializer = CommissionStripePayoutSerializer(data=data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        commission_id = serializer.validated_data["id"]

        try:
            commissions = Commission.objects.get(id=commission_id)
            user = commissions.user
            transfer = create_stripe_transfer(user, commissions)
            return Response({"data": transfer})
        except Exception as e:
            logger.error(f"Error creating stripe payout: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import stripe

from commission.models import Commission
from commission.serializers import CommissionStripePayoutSerializer
from commission.utlis import (
    retrieve_recipient_stripe,
    create_bank_account_link,
    create_stripe_transfer_from_commission,
    create_stripe_recipient
)
from utils.send_email import send_email

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

    def post(self, request):
        try:
            user = request.user
            logger.info(f"Receive request to create Stripe recipient account for user: {user.id}")

            user_stripe_recipient_id = user.stripe_account_id

            if not user_stripe_recipient_id:
                logger.info("Stripe recipient id not found, creating")
                stripe_recipient_id = create_stripe_recipient(user)
                user.stripe_account_id = stripe_recipient_id
                user.save()
                logger.info(f"Stripe recipient account added to User: {user.id}")

            logger.info("Successfully create Stripe recipient account")
            return Response({"detail": "Successfully create Stripe recipient account"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating Stripe recipient account: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StripeOnboardingEmailView(APIView):

    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        user = request.user

        recipient_account_id = user.stripe_account_id
        if not recipient_account_id:
            return Response({"error": "Stripe recipient account not found"}, status=status.HTTP_400_BAD_REQUEST)
        if user.stripe_onboard_status:
            return Response({"error": "You already onboarded"}, status=status.HTTP_400_BAD_REQUEST)
        try:

            account_link = create_bank_account_link(recipient_account_id)
            logger.info(f"User: {user.id} Stripe recipient account link: {account_link}")
            send_email(user=user, url=account_link, email_type="stripe_onboarding")
            logger.info("Stripe recipient email sent")

            return Response({"detail": "Email sent successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error to send email: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StripePayoutsView(APIView):

    permission_classes = (IsAuthenticated, )

    def post(self, request):

        data = request.data
        request_user = request.user
        serializer = CommissionStripePayoutSerializer(data=data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        commission_id = serializer.validated_data["id"]

        try:
            commission = Commission.objects.get(id=commission_id)
            commission_user = commission.user
            if commission_user != request_user:
                raise PermissionDenied("You can't submit payouts for this commission")

            transfer = create_stripe_transfer_from_commission(commission_user, commission)
            commission.stripe_transfer_id = transfer["id"]
            commission.paid = True
            commission.save()
            return Response({"transfer": transfer}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating stripe payout: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

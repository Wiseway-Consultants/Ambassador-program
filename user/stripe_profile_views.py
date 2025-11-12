import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import stripe

from commission.utlis import create_stripe_express_account
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
                        "error": "You doesn't have Express Stripe account"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            account = stripe.Account.retrieve(user_stripe_acc_id)
            logger.debug(f"Stripe Account retrieved: {account}")
            return Response(account)
        except Exception as e:
            logger.error(f"Error getting stripe_profile: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):

        try:
            user = request.user
            if not user.stripe_account_id:
                stripe_account = create_stripe_express_account(user=user)
                return Response({"stripe_id": stripe_account}, status=status.HTTP_201_CREATED)
            return Response(
                {"stripe_id": user.stripe_account_id, "message": "Account already exists"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error creating stripe profile: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StripeOnboardingView(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_stripe_acc_id = user.stripe_account_id
        if not user_stripe_acc_id:
            return Response({"error": "You don't have stripe account"}, status=status.HTTP_400_BAD_REQUEST)

        account_link = stripe.AccountLink.create(
            account=user_stripe_acc_id,  # The Express account ID
            refresh_url="https://savefryoil.com/ambassador-referrals/profile/",  # If user abandons onboarding
            return_url="https://savefryoil.com/ambassador-referrals/profile/",  # After onboarding completes
            type="account_onboarding"
        )
        send_email(
            user=user,
            url=account_link.get("url"),
            email_type="stripe_onboarding"
        )
        return Response({"account_link": account_link}, status=status.HTTP_200_OK)

import logging

from django.db import transaction
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from commission.models import Commission
from commission.serializers import CommissionListSerializer
from commission.utlis import create_stripe_express_account, create_stripe_recipient, create_bank_account_link
from prospect.models import Prospect
from prospect.permissions import IsSuperUser
from prospect.utils import get_invitation_user_chain_from_prospect, get_currency_by_country_code
from prospect.validation import validate_prospect, ValidationError
from utils.send_email import send_email

logger = logging.getLogger(__name__)

DIRECT_SALE_AMOUNT = 50
TOTAL_TEAM_REWARD_AMOUNT = 75
PERCENTAGE_COMMISSION_LEVELS = ["DIRECT SALE", 30, 20, 15, 12, 10, 8, 5]


class CommissionClaimView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):

        data = request.data
        logger.info(f"Received request to claim prospect for commission: {data}")
        request_user = request.user

        try:
            validate_prospect(data)  # Validate proper payload
        except (ValueError, TypeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        number_of_frylows = data.pop('number_of_frylows', 0)

        prospect_id = data['id']
        prospect = Prospect.objects.get(pk=prospect_id)

        try:  # Validate prospect

            if prospect.invited_by_user != request_user:
                raise ValidationError("You can't claim prospect that wasn't invited by you")

            if not prospect.deal_completed or prospect.claimed:
                raise ValidationError("Prospect's deal is not completed or already claimed.")

        except ValidationError as e:
            logger.error(f"Error to claim prospect for commission: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            currency = get_currency_by_country_code(prospect.country)
            users_invitation_chain = get_invitation_user_chain_from_prospect(prospect)
            commission_level = 0
            for user in users_invitation_chain:
                with transaction.atomic():

                    if commission_level == 0:  # Direct Sale
                        money_amount = DIRECT_SALE_AMOUNT * number_of_frylows
                    else:
                        pool_percentage = PERCENTAGE_COMMISSION_LEVELS[commission_level] / 100
                        money_amount = (TOTAL_TEAM_REWARD_AMOUNT * pool_percentage) * number_of_frylows
                    logger.info(f"Commission amount for user's id {user.id}: {currency} {money_amount}")
                    Commission.objects.create(
                        prospect=prospect,
                        number_of_frylows=number_of_frylows,
                        user=user,
                        commission_tree_level=commission_level,
                        money_amount=money_amount,
                        currency=currency
                    )
                    commission_level += 1
                    prospect.claimed = True
                    prospect.save()

                    if not user.stripe_account_id:
                        stripe_account_id = create_stripe_express_account(user)
                        logger.info(f"Stripe account for user {user.id} created: {stripe_account_id}")
                    else:
                        stripe_account_id = user.stripe_account_id
                        logger.info(f"Stripe account for user {user.id} already exists: {stripe_account_id}")

                logger.info(f"Successfully claimed prospect for commission: {prospect}")
            return Response({"detail": "success"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error to claim prospect for commission: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CommissionListView(ListAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = CommissionListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Commission.objects.all()

        return Commission.objects.filter(user=user)


class StripeRecipientView(APIView):
    permission_classes = [IsSuperUser, ]

    def post(self, request):
        try:
            data = request.data
            commission = Commission.objects.get(id=data['id'])
            if commission.paid:
                return Response({"error": "Commission already paid"}, status=status.HTTP_400_BAD_REQUEST)
            commission_recipient = commission.user
            stripe_recipient_id = commission_recipient.stripe_account_id
            if not stripe_recipient_id:

                logger.info("Stripe recipient id not found, creating")
                stripe_recipient_id = create_stripe_recipient(commission_recipient)
                commission_recipient.stripe_account_id = stripe_recipient_id
                commission_recipient.save()
                logger.info(f"Stripe recipient account added to User: {commission_recipient.id}")

            if not commission_recipient.stripe_onboard_status:
                account_link = create_bank_account_link(stripe_recipient_id)
                send_email(user=commission_recipient, url=account_link, email_type="stripe_onboarding")
                logger.info("Stripe recipient email sent")

            return Response({"detail": "Success, Ambassador receives an onboarding email"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error to create stripe_recipient for commission: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StripeOnboardingEmailView(APIView):

    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        user = request.user

        recipient_account_id = user.stripe_account_id
        if not recipient_account_id:
            return Response({"error": "Stripe recipient account not found"}, status=status.HTTP_200_OK)
        if user.stripe_onboard_status:
            return Response({"error": "You already onboarded"}, status=status.HTTP_200_OK)
        try:

            account_link = create_bank_account_link(recipient_account_id)
            logger.info(f"User: {user.id} Stripe recipient account link: {account_link}")
            send_email(user=user, url=account_link, email_type="stripe_onboarding")
            logger.info("Stripe recipient email sent")

            return Response({"detail": "Email sent successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error to send email: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

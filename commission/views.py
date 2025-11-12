import logging

from django.db import transaction
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from commission.models import Commission
from commission.serializers import CommissionListSerializer
from commission.utlis import create_stripe_express_account
from prospect.models import Prospect
from prospect.utils import get_invitation_user_chain_from_prospect, get_currency_by_country_code
from prospect.validation import validate_prospect, ValidationError

logger = logging.getLogger(__name__)

DIRECT_SALE_AMOUNT = 50
TOTAL_TEAM_REWARD_AMOUNT = 75
PERCENTAGE_COMMISSION_LEVELS = ["DIRECT SALE", 30, 20, 15, 12, 10, 8, 5]


class CommissionClaimView(APIView):
    permission_classes = [IsAuthenticated,]

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

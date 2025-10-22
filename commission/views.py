from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from commission.models import Commission
from prospect.models import Prospect
from prospect.permissions import IsStaffUser
from prospect.utils import get_invitation_user_chain_from_prospect
from prospect.validation import validate_prospect, ValidationError


class CommissionClaimView(APIView):
    permission_classes = [IsAuthenticated,]

    def post(self, request):

        data = request.data
        request_user = request.user

        if not validate_prospect(data):  # Validate proper payload
            return Response({'error': 'Invalid prospect'}, status=status.HTTP_400_BAD_REQUEST)

        number_of_frylows = data.pop('number_of_frylows', 0)

        prospect_id = data['id']
        prospect = Prospect.objects.get(pk=prospect_id)

        try:  # Validate prospect

            if prospect.invited_by_user != request_user:
                raise ValidationError("You can't claim prospect that wasn't invited by you")

            if not prospect.deal_completed or prospect.claimed:
                raise ValidationError("Prospect's deal is not completed or already claimed.")

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            users_invitation_chain = get_invitation_user_chain_from_prospect(prospect)
            commission_level = 0
            for user in users_invitation_chain:
                Commission.objects.create(
                    prospect=prospect,
                    number_of_frylows=number_of_frylows,
                    user=user,
                    commission_tree_level=commission_level,
                )
                commission_level += 1
            prospect.claimed = True
            prospect.save()
            return Response({"detail": "success"}, status=status.HTTP_201_CREATED)

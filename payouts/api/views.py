from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response

from payouts.api.serializers import (
    PayoutCreateHeadersSerializer,
    PayoutResponseSerializer,
    PayoutSerializer,
)
from payouts.models import Merchant
from payouts.services.idempotency import (
    begin_idempotency_window,
    store_idempotent_response,
)
from payouts.services.exceptions import InsufficientFundsError
from payouts.services.payouts import create_pending_payout


class PayoutViewSet(viewsets.ViewSet):
    serializer_class = PayoutSerializer

    def create(self, request):
        insufficient_funds = False

        header_serializer = PayoutCreateHeadersSerializer(
            data=PayoutCreateHeadersSerializer.from_request_headers(request.headers)
        )

        if not header_serializer.is_valid():
            errors = header_serializer.errors
            if "idempotency_key" in errors:
                return Response(
                    {"detail": "Missing or invalid Idempotency-Key header."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        merchant = get_object_or_404(Merchant, id=header_serializer.validated_data["merchant_id"])
        serializer = self.serializer_class(
            data=request.data,
            context={"merchant": merchant},
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            idempotency_result = begin_idempotency_window(
                merchant=merchant,
                key=header_serializer.validated_data["idempotency_key"],
            )

            if idempotency_result.state == "replay":
                payload = idempotency_result.replay_payload or {}
                return Response(
                    payload.get("body", {}),
                    status=payload.get("status_code", status.HTTP_200_OK),
                )

            if idempotency_result.state == "in_flight":
                return Response(
                    {"detail": "Request with this idempotency key is already in progress."},
                    status=status.HTTP_409_CONFLICT,
                )

            try:
                payout = create_pending_payout(
                    merchant=merchant,
                    amount_paise=serializer.validated_data["amount_paise"],
                    bank_account_id=serializer.validated_data["bank_account_id"],
                    idempotency_key=header_serializer.validated_data["idempotency_key"],
                )
            except InsufficientFundsError:
                # Do not retain a NULL response idempotency record for business rejections.
                # This prevents the same key from getting stuck in perpetual "in_flight".
                if idempotency_result.record is not None:
                    idempotency_result.record.delete()
                insufficient_funds = True
                payout = None

            if not insufficient_funds:
                response_payload = PayoutResponseSerializer(
                    {
                        "id": payout.id,
                        "status": payout.status,
                        "amount_paise": payout.amount_paise,
                        "created_at": payout.created_at,
                    }
                ).data

                if idempotency_result.record is not None:
                    store_idempotent_response(
                        record=idempotency_result.record,
                        body=response_payload,
                        status_code=status.HTTP_201_CREATED,
                    )
                return Response(response_payload, status=status.HTTP_201_CREATED)

        if insufficient_funds:
            return Response(
                {"detail": "Insufficient funds."},
                status=status.HTTP_400_BAD_REQUEST,
            )

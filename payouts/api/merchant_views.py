from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from payouts.api.merchant_serializers import (
    BankAccountOptionSerializer,
    LedgerEntrySerializer,
    MerchantBalanceSerializer,
    MerchantOptionSerializer,
    PayoutHistorySerializer,
)
from payouts.api.pagination import StandardResultsSetPagination
from payouts.models import Merchant
from payouts.services.merchant_queries import get_balance_snapshot


class MerchantListView(generics.ListAPIView):
    serializer_class = MerchantOptionSerializer
    pagination_class = None

    def get_queryset(self):
        return Merchant.objects.all().order_by("name")


class MerchantBalanceView(generics.GenericAPIView):
    serializer_class = MerchantBalanceSerializer

    def get(self, request, merchant_id):
        merchant = get_object_or_404(Merchant, id=merchant_id)
        payload = get_balance_snapshot(merchant=merchant)
        serializer = self.serializer_class(payload)
        return Response(serializer.data)


class MerchantLedgerView(generics.ListAPIView):
    serializer_class = LedgerEntrySerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        merchant = get_object_or_404(Merchant, id=self.kwargs["merchant_id"])
        return merchant.ledger_entries.all()


class MerchantPayoutHistoryView(generics.ListAPIView):
    serializer_class = PayoutHistorySerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        merchant = get_object_or_404(Merchant, id=self.kwargs["merchant_id"])
        return merchant.payouts.select_related("bank_account").all()


class MerchantBankAccountsView(generics.ListAPIView):
    serializer_class = BankAccountOptionSerializer
    pagination_class = None

    def get_queryset(self):
        merchant = get_object_or_404(Merchant, id=self.kwargs["merchant_id"])
        return merchant.bank_accounts.all().order_by("-is_primary", "id")

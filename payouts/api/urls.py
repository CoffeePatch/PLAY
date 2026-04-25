from django.urls import include, path
from rest_framework.routers import DefaultRouter

from payouts.api.merchant_views import (
    MerchantBalanceView,
    MerchantLedgerView,
    MerchantPayoutHistoryView,
)
from payouts.api.views import PayoutViewSet

router = DefaultRouter()
router.register("payouts", PayoutViewSet, basename="payouts")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "merchants/<uuid:merchant_id>/balance",
        MerchantBalanceView.as_view(),
        name="merchant-balance",
    ),
    path(
        "merchants/<uuid:merchant_id>/ledger",
        MerchantLedgerView.as_view(),
        name="merchant-ledger",
    ),
    path(
        "merchants/<uuid:merchant_id>/payouts",
        MerchantPayoutHistoryView.as_view(),
        name="merchant-payout-history",
    ),
]

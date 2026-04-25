from rest_framework import serializers

from payouts.models import LedgerEntry, Payout


class MerchantBalanceSerializer(serializers.Serializer):
    available_paise = serializers.IntegerField()
    held_paise = serializers.IntegerField()
    total_paise = serializers.IntegerField()


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "entry_type",
            "amount_paise",
            "description",
            "reference_id",
            "created_at",
        ]


class PayoutHistorySerializer(serializers.ModelSerializer):
    bank_account_id = serializers.IntegerField(source="bank_account.id")

    class Meta:
        model = Payout
        fields = [
            "id",
            "amount_paise",
            "status",
            "attempts",
            "idempotency_key",
            "bank_account_id",
            "created_at",
            "updated_at",
            "processed_at",
        ]

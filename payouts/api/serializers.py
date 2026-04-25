from rest_framework import serializers

from payouts.models import BankAccount


class PayoutSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1)
    bank_account_id = serializers.IntegerField(min_value=1)

    def validate_bank_account_id(self, value: int) -> int:
        merchant = self.context["merchant"]
        exists = BankAccount.objects.filter(id=value, merchant=merchant).exists()
        if not exists:
            raise serializers.ValidationError(
                "Bank account does not belong to merchant."
            )
        return value


class PayoutResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(format="hex_verbose")
    status = serializers.CharField()
    amount_paise = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class PayoutCreateHeadersSerializer(serializers.Serializer):
    idempotency_key = serializers.UUIDField()
    merchant_id = serializers.UUIDField()

    @staticmethod
    def from_request_headers(headers) -> dict:
        return {
            "idempotency_key": headers.get("Idempotency-Key"),
            "merchant_id": headers.get("X-Merchant-Id"),
        }

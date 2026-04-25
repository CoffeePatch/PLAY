import uuid

from django.db import models


class IdempotencyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "payouts.Merchant",
        on_delete=models.CASCADE,
        related_name="idempotency_records",
    )
    key = models.UUIDField()
    response_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "key"],
                name="unique_merchant_idempotency_key",
            )
        ]

    def __str__(self):
        return f"{self.merchant_id} - {self.key}"

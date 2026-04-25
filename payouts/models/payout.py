import uuid

from django.db import models
from django.db.models import Q

from .constants import PayoutStatus


class Payout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "payouts.Merchant",
        on_delete=models.CASCADE,
        related_name="payouts",
    )
    bank_account = models.ForeignKey(
        "payouts.BankAccount",
        on_delete=models.PROTECT,
        related_name="payouts",
    )
    amount_paise = models.BigIntegerField()
    status = models.CharField(
        max_length=16,
        choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING,
    )
    idempotency_key = models.UUIDField()
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(amount_paise__gt=0),
                name="payout_amount_paise_gt_zero",
            )
        ]

    def __str__(self):
        return f"{self.id} ({self.status})"

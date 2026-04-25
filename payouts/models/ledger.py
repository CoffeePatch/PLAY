import uuid

from django.db import models
from django.db.models import Q

from .constants import LedgerEntryType


class LedgerEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        "payouts.Merchant",
        on_delete=models.CASCADE,
        related_name="ledger_entries",
    )
    entry_type = models.CharField(max_length=16, choices=LedgerEntryType.choices)
    amount_paise = models.BigIntegerField()
    description = models.TextField(blank=True)
    reference_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(amount_paise__gt=0),
                name="ledger_entry_amount_paise_gt_zero",
            )
        ]

    def __str__(self):
        return f"{self.entry_type} {self.amount_paise}"

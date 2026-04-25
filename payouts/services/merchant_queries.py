from django.db import models
from django.db.models import BigIntegerField, Case, Sum, Value, When
from django.db.models.functions import Coalesce

from payouts.models import LedgerEntry, LedgerEntryType


def get_held_balance_paise(*, merchant_id) -> int:
    held = (
        LedgerEntry.objects.filter(merchant_id=merchant_id)
        .aggregate(
            held=Coalesce(
                Sum(
                    Case(
                        When(entry_type=LedgerEntryType.HOLD, then="amount_paise"),
                        When(entry_type=LedgerEntryType.RELEASE, then=-models.F("amount_paise")),
                        default=Value(0),
                        output_field=BigIntegerField(),
                    )
                ),
                Value(0),
                output_field=BigIntegerField(),
            )
        )
        .get("held", 0)
    )
    return int(held or 0)


def get_balance_snapshot(*, merchant) -> dict[str, int]:
    available_paise = int(
        merchant.__class__.objects.get_balance(merchant.id)
    )
    held_paise = get_held_balance_paise(merchant_id=merchant.id)
    total_paise = available_paise + held_paise
    return {
        "available_paise": available_paise,
        "held_paise": held_paise,
        "total_paise": total_paise,
    }

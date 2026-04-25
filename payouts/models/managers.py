from django.db import models
from django.db.models import BigIntegerField, Case, Sum, Value, When
from django.db.models.functions import Coalesce

from .constants import LedgerEntryType


class MerchantQuerySet(models.QuerySet):
    def get_balance(self, merchant_id):
        from .ledger import LedgerEntry

        balance = (
            LedgerEntry.objects.filter(merchant_id=merchant_id)
            .aggregate(
                balance=Coalesce(
                    Sum(
                        Case(
                            When(
                                entry_type=LedgerEntryType.CREDIT,
                                then="amount_paise",
                            ),
                            When(
                                entry_type=LedgerEntryType.RELEASE,
                                then="amount_paise",
                            ),
                            When(
                                entry_type=LedgerEntryType.DEBIT,
                                then=-models.F("amount_paise"),
                            ),
                            When(
                                entry_type=LedgerEntryType.HOLD,
                                then=-models.F("amount_paise"),
                            ),
                            default=Value(0),
                            output_field=BigIntegerField(),
                        )
                    ),
                    Value(0),
                    output_field=BigIntegerField(),
                )
            )
            .get("balance", 0)
        )
        return int(balance or 0)


class MerchantManager(models.Manager.from_queryset(MerchantQuerySet)):
    pass

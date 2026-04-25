from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, NAMESPACE_DNS, uuid5

from django.db import transaction

from payouts.models import BankAccount, LedgerEntry, LedgerEntryType, Merchant


@dataclass(frozen=True)
class MerchantSeed:
    name: str
    email: str
    bank_accounts: list[tuple[str, str, bool]]
    credit_amounts: list[int]


SEED_MERCHANTS: list[MerchantSeed] = [
    MerchantSeed(
        name="Aster Digital",
        email="finance@asterdigital.in",
        bank_accounts=[
            ("50110000000011", "HDFC0000123", True),
            ("011005500129", "ICIC0000456", False),
        ],
        credit_amounts=[120000, 85000, 54000, 99000, 63000],
    ),
    MerchantSeed(
        name="Bluefin Labs",
        email="ops@bluefinlabs.in",
        bank_accounts=[
            ("226000019901", "SBIN0000789", True),
            ("900001100221", "YESB0000321", False),
            ("001100772255", "UTIB0000199", False),
        ],
        credit_amounts=[44000, 125000, 71000, 39000, 56000, 132000],
    ),
    MerchantSeed(
        name="Comet Media",
        email="accounts@cometmedia.in",
        bank_accounts=[
            ("339901122233", "KKBK0000311", True),
            ("777700991122", "IDFB0000101", False),
        ],
        credit_amounts=[28000, 36000, 92000, 47000, 76000, 51000, 68000],
    ),
]


def _credit_reference(email: str, index: int) -> UUID:
    return uuid5(NAMESPACE_DNS, f"seed-credit:{email}:{index}")


def _seed_merchant(seed: MerchantSeed) -> tuple[Merchant, bool]:
    merchant, created = Merchant.objects.get_or_create(
        email=seed.email,
        defaults={"name": seed.name},
    )
    if merchant.name != seed.name:
        merchant.name = seed.name
        merchant.save(update_fields=["name"])
    return merchant, created


def _seed_bank_accounts(merchant: Merchant, seed: MerchantSeed) -> int:
    created_count = 0
    for account_number, ifsc, is_primary in seed.bank_accounts:
        _, created = BankAccount.objects.get_or_create(
            merchant=merchant,
            account_number=account_number,
            ifsc=ifsc,
            defaults={"is_primary": is_primary},
        )
        if created:
            created_count += 1
    return created_count


def _seed_credits(merchant: Merchant, seed: MerchantSeed) -> int:
    created_count = 0
    for index, amount_paise in enumerate(seed.credit_amounts, start=1):
        reference = _credit_reference(seed.email, index)
        _, created = LedgerEntry.objects.get_or_create(
            merchant=merchant,
            entry_type=LedgerEntryType.CREDIT,
            reference_id=reference,
            defaults={
                "amount_paise": amount_paise,
                "description": f"Seed credit {index}",
            },
        )
        if created:
            created_count += 1
    return created_count


@transaction.atomic
def seed_demo_data() -> dict[str, int]:
    merchants_created = 0
    bank_accounts_created = 0
    credits_created = 0

    for seed in SEED_MERCHANTS:
        merchant, created = _seed_merchant(seed)
        merchants_created += int(created)
        bank_accounts_created += _seed_bank_accounts(merchant, seed)
        credits_created += _seed_credits(merchant, seed)

    return {
        "merchants_created": merchants_created,
        "bank_accounts_created": bank_accounts_created,
        "credits_created": credits_created,
        "total_merchants": len(SEED_MERCHANTS),
    }

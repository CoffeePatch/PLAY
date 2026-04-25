from __future__ import annotations

import random
import time
from datetime import timedelta
from typing import Callable

from django.db import transaction
from django.utils import timezone

from payouts.models import LedgerEntry, LedgerEntryType, Payout, PayoutStatus

BankOutcome = str


def simulate_bank_outcome() -> BankOutcome:
    value = random.random()
    if value < 0.7:
        return "success"
    if value < 0.9:
        return "failure"
    return "hang"


@transaction.atomic
def claim_next_pending_payout() -> Payout | None:
    payout = (
        Payout.objects.select_for_update(skip_locked=True)
        .filter(status=PayoutStatus.PENDING)
        .order_by("created_at")
        .first()
    )
    if payout is None:
        return None

    payout.transition_to(PayoutStatus.PROCESSING)
    return payout


@transaction.atomic
def complete_payout_success(*, payout_id) -> bool:
    payout = (
        Payout.objects.select_for_update()
        .select_related("merchant")
        .filter(id=payout_id, status=PayoutStatus.PROCESSING)
        .first()
    )
    if payout is None:
        return False

    # Convert held funds into a finalized debit without mutating historical rows.
    LedgerEntry.objects.create(
        merchant=payout.merchant,
        entry_type=LedgerEntryType.RELEASE,
        amount_paise=payout.amount_paise,
        description="Release hold before payout debit",
        reference_id=payout.id,
    )
    LedgerEntry.objects.create(
        merchant=payout.merchant,
        entry_type=LedgerEntryType.DEBIT,
        amount_paise=payout.amount_paise,
        description="Payout completed",
        reference_id=payout.id,
    )

    payout.transition_to(PayoutStatus.COMPLETED)
    payout.processed_at = timezone.now()
    payout.save(update_fields=["processed_at", "updated_at"])
    return True


@transaction.atomic
def complete_payout_failure(*, payout_id) -> bool:
    payout = (
        Payout.objects.select_for_update()
        .select_related("merchant")
        .filter(id=payout_id, status=PayoutStatus.PROCESSING)
        .first()
    )
    if payout is None:
        return False

    LedgerEntry.objects.create(
        merchant=payout.merchant,
        entry_type=LedgerEntryType.RELEASE,
        amount_paise=payout.amount_paise,
        description="Payout failed; held funds released",
        reference_id=payout.id,
    )

    payout.transition_to(PayoutStatus.FAILED)
    payout.processed_at = timezone.now()
    payout.save(update_fields=["processed_at", "updated_at"])
    return True


def _apply_outcome_for_processing_payout(
    *,
    payout_id,
    outcome: BankOutcome,
    sleep_fn: Callable[[float], None],
) -> None:
    if outcome == "success":
        complete_payout_success(payout_id=payout_id)
    elif outcome == "failure":
        complete_payout_failure(payout_id=payout_id)
    elif outcome == "hang":
        sleep_fn(2.0)
        # Intentionally leave payout in PROCESSING for retry flow.
    else:
        raise ValueError(f"Unsupported bank outcome: {outcome}")


@transaction.atomic
def claim_next_stuck_processing_payout(*, stale_before) -> Payout | None:
    payout = (
        Payout.objects.select_for_update(skip_locked=True)
        .filter(status=PayoutStatus.PROCESSING, updated_at__lt=stale_before)
        .order_by("updated_at")
        .first()
    )
    if payout is None:
        return None

    payout.attempts += 1
    payout.save(update_fields=["attempts", "updated_at"])
    return payout


def process_pending_payouts_batch(
    *,
    batch_size: int = 20,
    outcome_fn: Callable[[], BankOutcome] = simulate_bank_outcome,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> int:
    processed = 0

    for _ in range(batch_size):
        payout = claim_next_pending_payout()
        if payout is None:
            break

        outcome = outcome_fn()
        _apply_outcome_for_processing_payout(
            payout_id=payout.id,
            outcome=outcome,
            sleep_fn=sleep_fn,
        )

        processed += 1

    return processed


def retry_stuck_payouts_batch(
    *,
    batch_size: int = 20,
    stale_after_seconds: int = 30,
    base_delay_seconds: float = 1.0,
    outcome_fn: Callable[[], BankOutcome] = simulate_bank_outcome,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> int:
    processed = 0
    stale_before = timezone.now() - timedelta(seconds=stale_after_seconds)

    for _ in range(batch_size):
        payout = claim_next_stuck_processing_payout(stale_before=stale_before)
        if payout is None:
            break

        if payout.attempts >= 3:
            complete_payout_failure(payout_id=payout.id)
        else:
            sleep_fn((2 ** payout.attempts) * base_delay_seconds)
            outcome = outcome_fn()
            _apply_outcome_for_processing_payout(
                payout_id=payout.id,
                outcome=outcome,
                sleep_fn=sleep_fn,
            )

        processed += 1

    return processed

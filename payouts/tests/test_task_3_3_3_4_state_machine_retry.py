import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from payouts.models import (
    BankAccount,
    InvalidStateTransition,
    LedgerEntry,
    LedgerEntryType,
    Merchant,
    Payout,
    PayoutStatus,
    VALID_TRANSITIONS,
)
from payouts.services.processor import retry_stuck_payouts_batch


class Task3334StateMachineRetryTests(TestCase):
    @staticmethod
    def _create_processing_payout(*, amount_paise: int = 6_000, attempts: int = 0) -> Payout:
        merchant = Merchant.objects.create(
            name=f"Merchant-{uuid.uuid4().hex[:8]}",
            email=f"merchant-{uuid.uuid4().hex[:8]}@example.com",
        )
        account = BankAccount.objects.create(
            merchant=merchant,
            account_number=f"ACC{uuid.uuid4().hex[:10]}",
            ifsc="HDFC0000123",
            is_primary=True,
        )

        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type=LedgerEntryType.CREDIT,
            amount_paise=10_000,
            description="Seed credit",
            reference_id=uuid.uuid4(),
        )

        payout = Payout.objects.create(
            merchant=merchant,
            bank_account=account,
            amount_paise=amount_paise,
            status=PayoutStatus.PENDING,
            idempotency_key=uuid.uuid4(),
            attempts=attempts,
        )
        payout.transition_to(PayoutStatus.PROCESSING)

        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type=LedgerEntryType.HOLD,
            amount_paise=amount_paise,
            description="Funds held for payout request",
            reference_id=payout.id,
        )

        Payout.objects.filter(id=payout.id).update(
            updated_at=timezone.now() - timedelta(seconds=90)
        )
        payout.refresh_from_db()
        return payout

    def test_valid_transitions_source_of_truth(self):
        self.assertEqual(
            VALID_TRANSITIONS,
            {
                PayoutStatus.PENDING: {PayoutStatus.PROCESSING},
                PayoutStatus.PROCESSING: {PayoutStatus.COMPLETED, PayoutStatus.FAILED},
            },
        )

    def test_invalid_transition_is_blocked(self):
        payout = self._create_processing_payout()
        payout.transition_to(PayoutStatus.COMPLETED)
        payout.refresh_from_db()

        with self.assertRaises(InvalidStateTransition):
            payout.transition_to(PayoutStatus.PENDING)

    def test_retry_increments_attempts_and_keeps_processing_on_hang(self):
        payout = self._create_processing_payout(attempts=0)
        sleep_calls: list[float] = []

        processed = retry_stuck_payouts_batch(
            outcome_fn=lambda: "hang",
            sleep_fn=lambda seconds: sleep_calls.append(seconds),
            base_delay_seconds=1.0,
            stale_after_seconds=30,
        )
        payout.refresh_from_db()

        self.assertEqual(processed, 1)
        self.assertEqual(payout.attempts, 1)
        self.assertEqual(payout.status, PayoutStatus.PROCESSING)
        self.assertEqual(sleep_calls, [2.0, 2.0])

    def test_retry_failure_after_max_attempts_releases_funds(self):
        payout = self._create_processing_payout(attempts=2)

        processed = retry_stuck_payouts_batch(
            outcome_fn=lambda: "hang",
            sleep_fn=lambda _: None,
            stale_after_seconds=30,
        )
        payout.refresh_from_db()

        self.assertEqual(processed, 1)
        self.assertEqual(payout.attempts, 3)
        self.assertEqual(payout.status, PayoutStatus.FAILED)
        self.assertIsNotNone(payout.processed_at)
        self.assertEqual(
            LedgerEntry.objects.filter(
                merchant=payout.merchant,
                reference_id=payout.id,
                entry_type=LedgerEntryType.RELEASE,
            ).count(),
            1,
        )

    def test_retry_can_complete_processing_payout(self):
        payout = self._create_processing_payout(attempts=1)

        processed = retry_stuck_payouts_batch(
            outcome_fn=lambda: "success",
            sleep_fn=lambda _: None,
            base_delay_seconds=0.0,
            stale_after_seconds=30,
        )
        payout.refresh_from_db()

        self.assertEqual(processed, 1)
        self.assertEqual(payout.attempts, 2)
        self.assertEqual(payout.status, PayoutStatus.COMPLETED)
        self.assertIsNotNone(payout.processed_at)
        self.assertEqual(
            LedgerEntry.objects.filter(
                merchant=payout.merchant,
                reference_id=payout.id,
                entry_type=LedgerEntryType.RELEASE,
            ).count(),
            1,
        )
        self.assertEqual(
            LedgerEntry.objects.filter(
                merchant=payout.merchant,
                reference_id=payout.id,
                entry_type=LedgerEntryType.DEBIT,
            ).count(),
            1,
        )

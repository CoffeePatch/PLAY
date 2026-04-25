import uuid
from unittest.mock import patch

from django.test import TestCase

from payouts.models import BankAccount, LedgerEntry, LedgerEntryType, Merchant, Payout, PayoutStatus
from payouts.services.processor import process_pending_payouts_batch, simulate_bank_outcome


class Task32PayoutProcessorTests(TestCase):
    @staticmethod
    def _create_pending_payout(amount_paise: int = 6_000) -> Payout:
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
        )
        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type=LedgerEntryType.HOLD,
            amount_paise=amount_paise,
            description="Funds held for payout request",
            reference_id=payout.id,
        )
        return payout

    def test_success_path_marks_completed_and_writes_release_and_debit(self):
        payout = self._create_pending_payout()

        processed = process_pending_payouts_batch(outcome_fn=lambda: "success")
        payout.refresh_from_db()

        self.assertEqual(processed, 1)
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

    def test_failure_path_marks_failed_and_releases_funds(self):
        payout = self._create_pending_payout()

        processed = process_pending_payouts_batch(outcome_fn=lambda: "failure")
        payout.refresh_from_db()

        self.assertEqual(processed, 1)
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
        self.assertEqual(
            LedgerEntry.objects.filter(
                merchant=payout.merchant,
                reference_id=payout.id,
                entry_type=LedgerEntryType.DEBIT,
            ).count(),
            0,
        )

    def test_hang_path_keeps_processing_and_writes_no_new_ledger_rows(self):
        payout = self._create_pending_payout()
        baseline_count = LedgerEntry.objects.filter(
            merchant=payout.merchant,
            reference_id=payout.id,
        ).count()

        processed = process_pending_payouts_batch(
            outcome_fn=lambda: "hang",
            sleep_fn=lambda _: None,
        )
        payout.refresh_from_db()

        self.assertEqual(processed, 1)
        self.assertEqual(payout.status, PayoutStatus.PROCESSING)
        self.assertIsNone(payout.processed_at)
        self.assertEqual(
            LedgerEntry.objects.filter(
                merchant=payout.merchant,
                reference_id=payout.id,
            ).count(),
            baseline_count,
        )

    def test_bank_outcome_distribution_thresholds(self):
        with patch("payouts.services.processor.random.random", return_value=0.69):
            self.assertEqual(simulate_bank_outcome(), "success")
        with patch("payouts.services.processor.random.random", return_value=0.89):
            self.assertEqual(simulate_bank_outcome(), "failure")
        with patch("payouts.services.processor.random.random", return_value=0.95):
            self.assertEqual(simulate_bank_outcome(), "hang")

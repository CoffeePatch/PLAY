import threading
import uuid

from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from payouts.models import BankAccount, IdempotencyRecord, LedgerEntry, LedgerEntryType, Merchant, Payout


class Task23PayoutAtomicityTests(TransactionTestCase):
    reset_sequences = True

    @staticmethod
    def _create_merchant_with_credit(*, credit_paise: int) -> tuple[Merchant, BankAccount]:
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
            amount_paise=credit_paise,
            description="Seed credit",
            reference_id=uuid.uuid4(),
        )
        return merchant, account

    @staticmethod
    def _post_payout(*, merchant_id, bank_account_id, amount_paise: int, idempotency_key: str):
        client = APIClient()
        return client.post(
            "/api/v1/payouts/",
            {"amount_paise": amount_paise, "bank_account_id": bank_account_id},
            format="json",
            HTTP_X_MERCHANT_ID=str(merchant_id),
            HTTP_IDEMPOTENCY_KEY=idempotency_key,
            HTTP_HOST="localhost",
        )

    def test_creates_pending_payout_and_hold_entry_atomically(self):
        merchant, account = self._create_merchant_with_credit(credit_paise=10_000)

        response = self._post_payout(
            merchant_id=merchant.id,
            bank_account_id=account.id,
            amount_paise=6_000,
            idempotency_key=str(uuid.uuid4()),
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(set(body.keys()), {"id", "status", "amount_paise", "created_at"})
        self.assertEqual(body["status"], "PENDING")
        self.assertEqual(body["amount_paise"], 6_000)

        payout = Payout.objects.get(id=body["id"])
        self.assertEqual(payout.status, "PENDING")
        self.assertTrue(
            LedgerEntry.objects.filter(
                merchant=merchant,
                entry_type=LedgerEntryType.HOLD,
                amount_paise=6_000,
                reference_id=payout.id,
            ).exists()
        )
        self.assertEqual(Merchant.objects.get_balance(merchant.id), 4_000)

    def test_insufficient_funds_returns_400_and_creates_no_hold(self):
        merchant, account = self._create_merchant_with_credit(credit_paise=1_000)

        response = self._post_payout(
            merchant_id=merchant.id,
            bank_account_id=account.id,
            amount_paise=2_000,
            idempotency_key=str(uuid.uuid4()),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("detail"), "Insufficient funds.")
        self.assertEqual(
            LedgerEntry.objects.filter(merchant=merchant, entry_type=LedgerEntryType.HOLD).count(),
            0,
        )
        self.assertEqual(Payout.objects.filter(merchant=merchant).count(), 0)
        self.assertEqual(IdempotencyRecord.objects.filter(merchant=merchant).count(), 0)

    def test_concurrent_requests_allow_only_one_success(self):
        if connection.vendor == "sqlite":
            self.skipTest("SQLite does not provide reliable row-level locking for this concurrency test.")

        merchant, account = self._create_merchant_with_credit(credit_paise=10_000)
        barrier = threading.Barrier(2)
        statuses: list[int] = []

        def worker():
            close_old_connections()
            try:
                barrier.wait()
                response = self._post_payout(
                    merchant_id=merchant.id,
                    bank_account_id=account.id,
                    amount_paise=6_000,
                    idempotency_key=str(uuid.uuid4()),
                )
                statuses.append(response.status_code)
            except Exception:
                statuses.append(-1)

        first = threading.Thread(target=worker)
        second = threading.Thread(target=worker)
        first.start()
        second.start()
        first.join()
        second.join()

        self.assertEqual(sorted(statuses), [400, 201])
        self.assertEqual(Payout.objects.filter(merchant=merchant, amount_paise=6_000).count(), 1)
        self.assertEqual(
            LedgerEntry.objects.filter(
                merchant=merchant,
                entry_type=LedgerEntryType.HOLD,
                amount_paise=6_000,
            ).count(),
            1,
        )
        self.assertEqual(Merchant.objects.get_balance(merchant.id), 4_000)

    def test_concurrent_same_idempotency_key_creates_single_payout(self):
        if connection.vendor == "sqlite":
            self.skipTest("SQLite does not provide reliable row-level locking for this concurrency test.")

        merchant, account = self._create_merchant_with_credit(credit_paise=10_000)
        shared_key = str(uuid.uuid4())
        barrier = threading.Barrier(2)
        statuses: list[int] = []

        def worker():
            close_old_connections()
            try:
                barrier.wait()
                response = self._post_payout(
                    merchant_id=merchant.id,
                    bank_account_id=account.id,
                    amount_paise=6_000,
                    idempotency_key=shared_key,
                )
                statuses.append(response.status_code)
            except Exception:
                statuses.append(-1)

        first = threading.Thread(target=worker)
        second = threading.Thread(target=worker)
        first.start()
        second.start()
        first.join()
        second.join()

        self.assertEqual(sorted(statuses), [201, 201])
        self.assertEqual(Payout.objects.filter(merchant=merchant, idempotency_key=shared_key).count(), 1)
        self.assertEqual(
            LedgerEntry.objects.filter(
                merchant=merchant,
                entry_type=LedgerEntryType.HOLD,
                amount_paise=6_000,
            ).count(),
            1,
        )

import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from payouts.models import BankAccount, LedgerEntry, LedgerEntryType, Merchant


class Task24MerchantEndpointsTests(TestCase):
    @staticmethod
    def _create_merchant_with_data() -> tuple[Merchant, BankAccount]:
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
            amount_paise=15_000,
            description="Seed credit",
            reference_id=uuid.uuid4(),
        )
        return merchant, account

    @staticmethod
    def _create_pending_payout(*, merchant: Merchant, account: BankAccount, amount_paise: int):
        client = APIClient()
        return client.post(
            "/api/v1/payouts/",
            {"amount_paise": amount_paise, "bank_account_id": account.id},
            format="json",
            HTTP_X_MERCHANT_ID=str(merchant.id),
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
            HTTP_HOST="localhost",
        )

    def test_balance_endpoint_returns_available_held_total(self):
        merchant, account = self._create_merchant_with_data()
        create_response = self._create_pending_payout(
            merchant=merchant,
            account=account,
            amount_paise=3_000,
        )
        self.assertEqual(create_response.status_code, 201)

        client = APIClient()
        response = client.get(
            f"/api/v1/merchants/{merchant.id}/balance",
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["available_paise"], 12_000)
        self.assertEqual(payload["held_paise"], 3_000)
        self.assertEqual(payload["total_paise"], 15_000)

    def test_ledger_endpoint_is_paginated(self):
        merchant, account = self._create_merchant_with_data()
        create_response = self._create_pending_payout(
            merchant=merchant,
            account=account,
            amount_paise=3_000,
        )
        self.assertEqual(create_response.status_code, 201)

        client = APIClient()
        response = client.get(
            f"/api/v1/merchants/{merchant.id}/ledger?page=1&page_size=1",
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("count", payload)
        self.assertIn("results", payload)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(len(payload["results"]), 1)

    def test_payout_history_endpoint_is_paginated_with_status(self):
        merchant, account = self._create_merchant_with_data()
        create_response = self._create_pending_payout(
            merchant=merchant,
            account=account,
            amount_paise=3_000,
        )
        self.assertEqual(create_response.status_code, 201)

        client = APIClient()
        response = client.get(
            f"/api/v1/merchants/{merchant.id}/payouts?page=1&page_size=1",
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("count", payload)
        self.assertIn("results", payload)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(len(payload["results"]), 1)
        row = payload["results"][0]
        self.assertEqual(row["status"], "PENDING")
        self.assertIn("bank_account_id", row)

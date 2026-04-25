from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payto_engine.settings")

import django

django.setup()

from django.db import close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient

from payouts.models import BankAccount, IdempotencyRecord, LedgerEntry, LedgerEntryType, Merchant, Payout


@dataclass
class CheckResult:
    task: str
    passed: bool
    message: str


def _new_client() -> APIClient:
    close_old_connections()
    return APIClient()


def _headers(merchant_id: str, idempotency_key: str | None = None) -> dict:
    headers = {"HTTP_X_MERCHANT_ID": merchant_id}
    if idempotency_key is not None:
        headers["HTTP_IDEMPOTENCY_KEY"] = idempotency_key
    return headers


def _create_merchant_with_funds(amount_paise: int) -> tuple[Merchant, BankAccount]:
    merchant = Merchant.objects.create(
        name=f"Merchant {uuid.uuid4().hex[:8]}",
        email=f"merchant-{uuid.uuid4().hex[:8]}@example.com",
    )
    bank_account = BankAccount.objects.create(
        merchant=merchant,
        account_number=f"ACC{uuid.uuid4().hex[:12]}",
        ifsc="HDFC0000123",
        is_primary=True,
    )
    LedgerEntry.objects.create(
        merchant=merchant,
        entry_type=LedgerEntryType.CREDIT,
        amount_paise=amount_paise,
        description="Test funding credit",
        reference_id=uuid.uuid4(),
    )
    return merchant, bank_account


def _post_payout(client: APIClient, merchant: Merchant, bank_account: BankAccount, amount: int, key: str | None):
    return client.post(
        "/api/v1/payouts/",
        data={"amount_paise": amount, "bank_account_id": bank_account.id},
        format="json",
        **_headers(str(merchant.id), key),
    )


def verify_task_2_1() -> list[CheckResult]:
    results: list[CheckResult] = []

    merchant, account = _create_merchant_with_funds(50000)
    other_merchant, other_account = _create_merchant_with_funds(50000)
    client = _new_client()

    # 2.1.1 validation: positive amount + bank account ownership
    res_negative = _post_payout(client, merchant, account, -1, str(uuid.uuid4()))
    ok_negative = res_negative.status_code == 400 and "amount_paise" in res_negative.json()
    results.append(
        CheckResult(
            "2.1.1",
            ok_negative,
            f"Negative amount validation status={res_negative.status_code}",
        )
    )

    res_wrong_account = client.post(
        "/api/v1/payouts/",
        data={"amount_paise": 1000, "bank_account_id": other_account.id},
        format="json",
        **_headers(str(merchant.id), str(uuid.uuid4())),
    )
    ok_wrong_account = (
        res_wrong_account.status_code == 400
        and "bank_account_id" in res_wrong_account.json()
    )
    results.append(
        CheckResult(
            "2.1.1",
            ok_wrong_account,
            f"Bank ownership validation status={res_wrong_account.status_code}",
        )
    )

    # 2.1.2 endpoint create works
    res_valid = _post_payout(client, merchant, account, 1000, str(uuid.uuid4()))
    body = res_valid.json() if res_valid.status_code == 201 else {}
    ok_create = res_valid.status_code == 201 and all(k in body for k in ["id", "status", "amount_paise", "created_at"])
    results.append(
        CheckResult(
            "2.1.2",
            ok_create,
            f"POST /api/v1/payouts status={res_valid.status_code}",
        )
    )

    # 2.1.3 missing Idempotency-Key -> 400
    res_missing_key = client.post(
        "/api/v1/payouts/",
        data={"amount_paise": 1000, "bank_account_id": account.id},
        format="json",
        **_headers(str(other_merchant.id), None),
    )
    ok_missing_key = res_missing_key.status_code == 400
    results.append(
        CheckResult(
            "2.1.3",
            ok_missing_key,
            f"Missing Idempotency-Key status={res_missing_key.status_code}",
        )
    )

    return results


def verify_task_2_2() -> list[CheckResult]:
    results: list[CheckResult] = []
    client = _new_client()

    # 2.2.1 replay exact same response
    merchant, account = _create_merchant_with_funds(50000)
    idem_key = str(uuid.uuid4())
    r1 = _post_payout(client, merchant, account, 1200, idem_key)
    r2 = _post_payout(client, merchant, account, 1200, idem_key)
    same_body = r1.json() == r2.json()
    same_status = r1.status_code == r2.status_code
    payout_count = Payout.objects.filter(merchant=merchant, idempotency_key=idem_key).count()
    results.append(
        CheckResult(
            "2.2.1",
            r1.status_code == 201 and same_status and same_body and payout_count == 1,
            f"Replay statuses=({r1.status_code},{r2.status_code}) payouts={payout_count}",
        )
    )

    # 2.2.2 expired key should be treated as new
    merchant2, account2 = _create_merchant_with_funds(50000)
    exp_key = str(uuid.uuid4())
    e1 = _post_payout(client, merchant2, account2, 1300, exp_key)
    record = IdempotencyRecord.objects.get(merchant=merchant2, key=exp_key)
    IdempotencyRecord.objects.filter(pk=record.pk).update(created_at=timezone.now() - timedelta(hours=25))
    e2 = _post_payout(client, merchant2, account2, 1300, exp_key)
    payouts_same_key = Payout.objects.filter(merchant=merchant2, idempotency_key=exp_key)
    different_ids = e1.status_code == 201 and e2.status_code == 201 and e1.json().get("id") != e2.json().get("id")
    results.append(
        CheckResult(
            "2.2.2",
            different_ids and payouts_same_key.count() == 2,
            f"Expired key statuses=({e1.status_code},{e2.status_code}) payouts={payouts_same_key.count()}",
        )
    )

    # 2.2.3 in-flight record should return 409
    merchant3, account3 = _create_merchant_with_funds(50000)
    inflight_key = str(uuid.uuid4())
    IdempotencyRecord.objects.create(merchant=merchant3, key=inflight_key, response_data=None)
    i1 = _post_payout(client, merchant3, account3, 1000, inflight_key)
    results.append(
        CheckResult(
            "2.2.3",
            i1.status_code == 409,
            f"In-flight duplicate status={i1.status_code}",
        )
    )

    # 2.2.4 successful create persists response_data in idempotency record
    merchant4, account4 = _create_merchant_with_funds(50000)
    persist_key = str(uuid.uuid4())
    p1 = _post_payout(client, merchant4, account4, 1500, persist_key)
    persisted = IdempotencyRecord.objects.get(merchant=merchant4, key=persist_key)
    has_payload = bool(persisted.response_data) and persisted.response_data.get("status_code") == 201
    matches_id = has_payload and persisted.response_data.get("body", {}).get("id") == p1.json().get("id")
    results.append(
        CheckResult(
            "2.2.4",
            p1.status_code == 201 and has_payload and matches_id,
            f"Persisted response status={p1.status_code} has_payload={has_payload}",
        )
    )

    # 2.2 race safety on insert with same key
    merchant5, account5 = _create_merchant_with_funds(50000)
    race_key = str(uuid.uuid4())
    barrier = threading.Barrier(2)
    race_statuses: list[int] = []

    def race_worker():
        c = _new_client()
        try:
            barrier.wait()
            resp = _post_payout(c, merchant5, account5, 1100, race_key)
            race_statuses.append(resp.status_code)
        except Exception:
            race_statuses.append(-1)

    t1 = threading.Thread(target=race_worker)
    t2 = threading.Thread(target=race_worker)
    t1.start(); t2.start(); t1.join(); t2.join()

    race_payout_count = Payout.objects.filter(merchant=merchant5, idempotency_key=race_key).count()
    race_ok = (
        len(race_statuses) == 2
        and race_payout_count == 1
        and all(s in {201, 409} for s in race_statuses)
    )
    results.append(
        CheckResult(
            "2.2.race",
            race_ok,
            f"Race statuses={sorted(race_statuses)} payout_count={race_payout_count}",
        )
    )

    return results


def verify_task_2_3() -> list[CheckResult]:
    results: list[CheckResult] = []
    client = _new_client()

    # 2.3.1/2.3.2/2.3.3/2.3.4 concurrency overdraft safety
    merchant, account = _create_merchant_with_funds(10000)
    barrier = threading.Barrier(2)
    statuses: list[int] = []

    def worker(key: str):
        c = _new_client()
        try:
            barrier.wait()
            resp = _post_payout(c, merchant, account, 6000, key)
            statuses.append(resp.status_code)
        except Exception:
            statuses.append(-1)

    t1 = threading.Thread(target=worker, args=(str(uuid.uuid4()),))
    t2 = threading.Thread(target=worker, args=(str(uuid.uuid4()),))
    t1.start(); t2.start(); t1.join(); t2.join()

    hold_count = LedgerEntry.objects.filter(
        merchant=merchant,
        entry_type=LedgerEntryType.HOLD,
        amount_paise=6000,
    ).count()
    available = Merchant.objects.get_balance(merchant.id)
    one_success_one_fail = len(statuses) == 2 and sorted(statuses) == [400, 201]
    results.append(
        CheckResult(
            "2.3.1-2.3.4",
            one_success_one_fail and hold_count == 1 and available == 4000,
            f"Statuses={sorted(statuses)} hold_count={hold_count} available={available}",
        )
    )

    # 2.3.5 transaction writes HOLD + PENDING + idempotency record
    merchant2, account2 = _create_merchant_with_funds(50000)
    key = str(uuid.uuid4())
    resp = _post_payout(client, merchant2, account2, 2500, key)
    body = resp.json() if resp.status_code == 201 else {}
    payout_id = body.get("id")
    hold_exists = LedgerEntry.objects.filter(
        merchant=merchant2,
        entry_type=LedgerEntryType.HOLD,
        reference_id=payout_id,
        amount_paise=2500,
    ).exists()
    payout_exists = Payout.objects.filter(merchant=merchant2, id=payout_id, status="PENDING").exists()
    idem_exists = IdempotencyRecord.objects.filter(merchant=merchant2, key=key).exists()
    results.append(
        CheckResult(
            "2.3.5",
            resp.status_code == 201 and hold_exists and payout_exists and idem_exists,
            f"status={resp.status_code} hold={hold_exists} payout={payout_exists} idem={idem_exists}",
        )
    )

    # 2.3.6 response shape consistency
    has_fields = all(k in body for k in ["id", "status", "amount_paise", "created_at"])
    results.append(
        CheckResult(
            "2.3.6",
            resp.status_code == 201 and has_fields,
            f"status={resp.status_code} fields_ok={has_fields}",
        )
    )

    return results


def verify_task_2_4() -> list[CheckResult]:
    results: list[CheckResult] = []
    client = _new_client()

    merchant, account = _create_merchant_with_funds(12000)
    # Create one payout to add hold and payout history data.
    _post_payout(client, merchant, account, 3000, str(uuid.uuid4()))

    # 2.4.1 balance endpoint
    balance_resp = client.get(f"/api/v1/merchants/{merchant.id}/balance")
    balance_body = balance_resp.json() if balance_resp.status_code == 200 else {}
    balance_keys_ok = all(k in balance_body for k in ["available_paise", "held_paise", "total_paise"])
    total_ok = balance_keys_ok and balance_body["available_paise"] + balance_body["held_paise"] == balance_body["total_paise"]
    results.append(
        CheckResult(
            "2.4.1",
            balance_resp.status_code == 200 and balance_keys_ok and total_ok,
            f"Balance status={balance_resp.status_code} body={balance_body}",
        )
    )

    # 2.4.2 ledger endpoint is paginated and returns entries
    ledger_resp = client.get(f"/api/v1/merchants/{merchant.id}/ledger")
    ledger_body = ledger_resp.json() if ledger_resp.status_code == 200 else {}
    ledger_paginated = all(k in ledger_body for k in ["count", "results"])
    results.append(
        CheckResult(
            "2.4.2",
            ledger_resp.status_code == 200 and ledger_paginated and ledger_body.get("count", 0) >= 2,
            f"Ledger status={ledger_resp.status_code} count={ledger_body.get('count')}",
        )
    )

    # 2.4.3 payouts endpoint is paginated and returns status history
    payouts_resp = client.get(f"/api/v1/merchants/{merchant.id}/payouts")
    payouts_body = payouts_resp.json() if payouts_resp.status_code == 200 else {}
    payouts_paginated = all(k in payouts_body for k in ["count", "results"])
    has_status = payouts_paginated and len(payouts_body.get("results", [])) > 0 and "status" in payouts_body["results"][0]
    results.append(
        CheckResult(
            "2.4.3",
            payouts_resp.status_code == 200 and payouts_paginated and has_status,
            f"Payout history status={payouts_resp.status_code} count={payouts_body.get('count')}",
        )
    )

    return results


def main() -> int:
    # Clean slate for repeatable verification.
    Payout.objects.all().delete()
    LedgerEntry.objects.all().delete()
    IdempotencyRecord.objects.all().delete()
    BankAccount.objects.all().delete()
    Merchant.objects.all().delete()

    checks = []
    checks.extend(verify_task_2_1())
    checks.extend(verify_task_2_2())
    checks.extend(verify_task_2_3())
    checks.extend(verify_task_2_4())

    print("\nPHASE 2 VERIFICATION RESULTS")
    print("=" * 36)
    failed = 0
    for c in checks:
        status = "PASS" if c.passed else "FAIL"
        print(f"[{status}] Task {c.task}: {c.message}")
        if not c.passed:
            failed += 1

    print("-" * 36)
    print(f"Total checks: {len(checks)} | Failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

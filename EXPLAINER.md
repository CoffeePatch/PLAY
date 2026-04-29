# EXPLAINER

## Required answers (with code references)

1. Ledger
Balance is derived entirely in the database using SUM/CASE with credits, debits, holds, and releases. This avoids Python-side arithmetic and keeps the invariant intact. See [payouts/models/managers.py](payouts/models/managers.py#L8-L44).

2. Lock
Concurrent payouts are serialized by row-level locks on the merchant and the selected bank account via `select_for_update()`. The available balance check happens under the lock before creating the payout and hold. See [payouts/services/payouts.py](payouts/services/payouts.py#L6-L29).

3. Idempotency
Idempotency records are stored per-merchant and keyed by UUID. A second request with the same key replays the stored response, while an in-flight request returns a 409-style response. TTL is enforced at 24 hours. See [payouts/services/idempotency.py](payouts/services/idempotency.py#L11-L81).

4. State machine
Legal state transitions are encoded in `VALID_TRANSITIONS`, and `transition_to()` rejects any backwards/invalid move. This blocks failed-to-completed and other illegal transitions. See [payouts/models/payout.py](payouts/models/payout.py#L9-L56).

5. AI audit
AI suggested adding `load_dotenv()` in Django settings but did not add the `python-dotenv` dependency to the shared `requirements.txt`. That broke Celery containers at runtime with `ModuleNotFoundError: No module named 'dotenv'`, so background processing never ran. I fixed it by adding the dependency and restarting the worker/beat containers. See [payto_engine/settings.py](payto_engine/settings.py#L1-L7) and [requirements.txt](requirements.txt#L1-L7).

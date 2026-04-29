# PLAY Payout Engine

Production-minded payout engine with ledger accounting, idempotent requests, and background processing.

## What it does

- Ledger-based balance tracking in paise (integer only)
- Idempotent payout creation with safe retries
- Background processing with retries and state-machine enforcement
- React dashboard for balances, ledger, and payout history

## Live URLs

- Frontend: https://play-green-phi.vercel.app
- API: https://play-production-fb7d.up.railway.app/api/v1

## Payout lifecycle

- PENDING: payout created and funds held
- PROCESSING: worker picked it up
- COMPLETED: hold released + debit posted
- FAILED: hold released

Stuck payouts are retried after 30 seconds with exponential backoff (max 3 attempts).

## API quick reference

Note: `/merchants` endpoints do not use a trailing slash, while `/payouts/` does.

- GET `/merchants`
- GET `/merchants/{merchant_id}/balance`
- GET `/merchants/{merchant_id}/bank-accounts`
- GET `/merchants/{merchant_id}/ledger`
- GET `/merchants/{merchant_id}/payouts`
- POST `/payouts/`
  - Headers: `X-Merchant-Id`, `Idempotency-Key`
  - Body: `{ "amount_paise": 5000, "bank_account_id": 1 }`

Example payout request:

```bash
curl -X POST "https://play-production-fb7d.up.railway.app/api/v1/payouts/" \
  -H "Content-Type: application/json" \
  -H "X-Merchant-Id: <merchant-uuid>" \
  -H "Idempotency-Key: <uuid>" \
  -d "{\"amount_paise\": 5000, \"bank_account_id\": 1}"
```

## Local development

Backend + workers:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

docker compose up -d postgres redis
python manage.py migrate
python manage.py seed_data

docker compose up -d celery_worker celery_beat
python manage.py runserver 0.0.0.0:8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment variables

Backend:

- `SECRET_KEY`
- `DEBUG` (set to `false` in production)
- `ALLOWED_HOSTS` (comma-separated)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `CORS_ALLOWED_ORIGINS` (comma-separated, no trailing slashes)

Frontend:

- `VITE_API_BASE_URL` (example: `https://play-production-fb7d.up.railway.app/api/v1`)
- `VITE_API_TIMEOUT_MS`

## Tests

```bash
python manage.py test payouts.tests
```

## Operations

- Workers must be running for payouts to leave `PROCESSING`.
- If workers are down, payouts can remain in `PROCESSING` until they restart.

## Force-process pending payouts (one-liner)

```bash
python manage.py shell -c "from payouts.services.processor import process_pending_payouts_batch; print(process_pending_payouts_batch())"
```

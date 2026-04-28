# PLAY

## Local dev (backend + frontend + workers)

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

```bash
cd frontend
npm install
npm run dev
```

## Force-process pending payouts (one-liner)

```bash
python manage.py shell -c "from payouts.services.processor import process_pending_payouts_batch; print(process_pending_payouts_batch())"
```

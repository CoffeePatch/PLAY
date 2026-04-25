from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.db import IntegrityError
from django.utils import timezone

from payouts.models import IdempotencyRecord

IDEMPOTENCY_TTL_HOURS = 24


@dataclass(frozen=True)
class IdempotencyResult:
    state: str
    record: IdempotencyRecord | None = None
    replay_payload: dict | None = None


def _is_expired(record: IdempotencyRecord) -> bool:
    cutoff = timezone.now() - timedelta(hours=IDEMPOTENCY_TTL_HOURS)
    return record.created_at < cutoff


def begin_idempotency_window(*, merchant, key) -> IdempotencyResult:
    existing = (
        IdempotencyRecord.objects.select_for_update()
        .filter(merchant=merchant, key=key)
        .first()
    )

    if existing is not None:
        if _is_expired(existing):
            existing.delete()
        elif existing.response_data:
            return IdempotencyResult(
                state="replay",
                replay_payload=existing.response_data,
            )
        else:
            return IdempotencyResult(state="in_flight")

    try:
        record = IdempotencyRecord.objects.create(
            merchant=merchant,
            key=key,
            response_data=None,
        )
        return IdempotencyResult(state="created", record=record)
    except IntegrityError:
        # Another transaction won the insert race. Re-read and respond deterministically.
        record = IdempotencyRecord.objects.get(merchant=merchant, key=key)
        if _is_expired(record):
            record.delete()
            record = IdempotencyRecord.objects.create(
                merchant=merchant,
                key=key,
                response_data=None,
            )
            return IdempotencyResult(state="created", record=record)
        if record.response_data:
            return IdempotencyResult(
                state="replay",
                replay_payload=record.response_data,
            )
        return IdempotencyResult(state="in_flight")


def store_idempotent_response(*, record: IdempotencyRecord, body: dict, status_code: int) -> None:
    record.response_data = {
        "status_code": status_code,
        "body": body,
    }
    record.save(update_fields=["response_data"])

from celery import shared_task

from payouts.services.processor import process_pending_payouts_batch, retry_stuck_payouts_batch


@shared_task(name="payouts.tasks.process_pending_payouts")
def process_pending_payouts() -> int:
    return process_pending_payouts_batch()


@shared_task(name="payouts.tasks.retry_stuck_payouts")
def retry_stuck_payouts() -> int:
    return retry_stuck_payouts_batch()

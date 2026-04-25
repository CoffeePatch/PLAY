from celery import shared_task


@shared_task(name="payouts.tasks.process_pending_payouts")
def process_pending_payouts() -> int:
    # Placeholder scheduler target for task 3.1; business logic is implemented next.
    return 0

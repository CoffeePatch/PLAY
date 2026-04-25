from payouts.models import BankAccount, LedgerEntry, LedgerEntryType, Merchant, Payout

from .exceptions import InsufficientFundsError


def create_pending_payout(*, merchant, amount_paise: int, bank_account_id: int, idempotency_key):
    # Lock merchant row first so concurrent payout requests serialize per merchant.
    locked_merchant = Merchant.objects.select_for_update().get(id=merchant.id)
    available_balance = Merchant.objects.get_balance(locked_merchant.id)
    if amount_paise > available_balance:
        raise InsufficientFundsError("Insufficient funds for payout request.")

    bank_account = BankAccount.objects.select_for_update().get(
        id=bank_account_id,
        merchant=locked_merchant,
    )
    payout = Payout.objects.create(
        merchant=locked_merchant,
        bank_account=bank_account,
        amount_paise=amount_paise,
        idempotency_key=idempotency_key,
    )
    LedgerEntry.objects.create(
        merchant=locked_merchant,
        entry_type=LedgerEntryType.HOLD,
        amount_paise=amount_paise,
        description="Funds held for payout request",
        reference_id=payout.id,
    )
    return payout

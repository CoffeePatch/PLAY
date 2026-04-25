from django.db import models


class BankAccount(models.Model):
    merchant = models.ForeignKey(
        "payouts.Merchant",
        on_delete=models.CASCADE,
        related_name="bank_accounts",
    )
    account_number = models.CharField(max_length=32)
    ifsc = models.CharField(max_length=16)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ifsc} - {self.account_number}"

from django.core.management.base import BaseCommand

from payouts.services import seed_demo_data


class Command(BaseCommand):
    help = "Seed demo merchants, bank accounts, and ledger credits."

    def handle(self, *args, **options):
        stats = seed_demo_data()
        self.stdout.write(self.style.SUCCESS("Seed data completed."))
        self.stdout.write(
            "Created merchants: "
            f"{stats['merchants_created']}"
        )
        self.stdout.write(
            "Created bank accounts: "
            f"{stats['bank_accounts_created']}"
        )
        self.stdout.write(
            "Created credit entries: "
            f"{stats['credits_created']}"
        )
        self.stdout.write(
            "Configured merchants in seed set: "
            f"{stats['total_merchants']}"
        )

from django.core.management.base import BaseCommand
from datetime import date
from trainer.models import Trainer, TrainerPayment

class Command(BaseCommand):
    help = "Create yearly payments for approved trainers"

    def handle(self, *args, **kwargs):
        year = date.today().year

        trainers = Trainer.objects.filter(status="approved")

        for trainer in trainers:
            for month in range(1, 13):
                TrainerPayment.objects.get_or_create(
                    trainer=trainer,
                    year=year,
                    month=month,
                    defaults={
                        "salary": trainer.expecting_salary,
                        "status": "pending",
                    }
                )

        self.stdout.write(self.style.SUCCESS("Trainer payments created"))

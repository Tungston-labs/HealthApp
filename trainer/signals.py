# trainer/signals.py
from datetime import date
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trainer, TrainerPayment

@receiver(post_save, sender=Trainer)
def create_payments_on_approval(sender, instance, **kwargs):
    if instance.status != "approved":
        return

    approved_date = instance.updated_at.date()
    year = approved_date.year
    start_month = approved_date.month

    for month in range(start_month, 13):
        TrainerPayment.objects.get_or_create(
            trainer=instance,
            year=year,
            month=month,
            defaults={
                "salary": instance.expecting_salary,
                "approved_date": approved_date,
                "status": "pending",
            }
        )

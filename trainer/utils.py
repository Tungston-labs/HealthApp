from django.core.mail import send_mail
from django.conf import settings

def send_trainer_invoice_email(trainer_email, subject, message):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [trainer_email],
        fail_silently=False,
    )




def get_plan_amount(plan, booking_type):
    if booking_type == "single":
        return plan.single_price
    elif booking_type == "couple":
        return plan.couple_price
    elif booking_type == "group":
        return plan.group_price
    else:
        raise ValueError("Invalid booking type")

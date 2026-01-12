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

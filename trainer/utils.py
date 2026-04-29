from django.core.mail import send_mail
from django.conf import settings
from .models import SlotBooking
import datetime
from datetime import timedelta

def send_trainer_invoice_email(trainer_email, subject, message):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [trainer_email],
        fail_silently=False,
    )


#  to get plan amount from trainer model

# def get_plan_amount(trainer, booking_type):
#     if booking_type == "single":
#         return trainer.single_price
#     elif booking_type == "couple":
#         return trainer.couple_price
#     elif booking_type == "group":
#         return trainer.group_price
#     else:
#         raise ValueError("Invalid booking type")
def get_plan_amount(trainer, booking_type):
    if not booking_type:
        raise ValueError("Booking type is missing")

    booking_type = booking_type.lower().strip()

    price_map = {
        "single": trainer.single_price,
        "couple": trainer.couple_price,
        "group": trainer.group_price,
    }

    if booking_type not in price_map:
        raise ValueError(
            f"Invalid booking type: {booking_type}. "
            f"Expected one of {list(price_map.keys())}"
        )

    return price_map[booking_type]
   
    

# to create booking internally

def create_trainer_bookings(
    client, trainer, plan,
    start_date, time_slot, slot_days,
    payment
):
    time_slot_obj = datetime.strptime(time_slot, "%H:%M").time()
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()

    weekday_map = {"mon":0,"tue":1,"wed":2,"thu":3,"fri":4,"sat":5,"sun":6}

    if plan.plan_type == "6_days":
        slot_days = ["mon","tue","wed","thu","fri","sat"]

    selected_weekdays = [weekday_map[d] for d in slot_days]

    max_sessions = trainer.no_of_section
    session_dates = []

    d = start_date_obj
    filled = 0

    while filled < max_sessions:
        if d.weekday() in selected_weekdays:
            session_dates.append(d)
            filled += 1
        d += timedelta(days=1)

    # 🔒 Conflict check
    if SlotBooking.objects.filter(
        trainer=trainer,
        date__in=session_dates,
        time=time_slot_obj
    ).exists():
        raise ValueError("Trainer already booked for selected slots")

    for date in session_dates:
        SlotBooking.objects.create(
            trainer=trainer,
            client=client,
            plan=plan,
            booking_type=payment.booking_type,
            amount_paid=payment.amount,
            payment=payment,
            date=date,
            time=time_slot_obj,
            payment_status="paid"
        )

    return len(session_dates)

from django.db import models
from plan.models import Plan
from django.contrib.auth import get_user_model
from datetime import time
from client.models import Client

User = get_user_model()

class TrainerCertificate(models.Model):
    image_url = models.URLField(max_length=500, null=True, blank=True)

class Trainer(models.Model):
    SECTION_CHOICES = (
        ('15', '15 min'),
        ('20', '20 min'),
        ('30', '30 min'),
        ('45', '45 min'),
        ('60', '60 min'),
    )
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    name = models.CharField(max_length=200)
    phno = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    dob = models.DateField()
    training_field = models.ForeignKey(
            Plan,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name="trainers"
        )    
    section_timing = models.CharField(max_length=5, choices=SECTION_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    location = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True,null=True)
    landmark = models.CharField(max_length=255, blank=True,null=True)
    city = models.CharField(max_length=100, blank=True,null=True)
    pincode = models.CharField(max_length=10, blank=True,null=True)
    expecting_salary = models.DecimalField(max_digits=10, decimal_places=2)
    no_of_section = models.PositiveIntegerField()

    certificates = models.ManyToManyField(TrainerCertificate, blank=True)
    adar_number = models.CharField(max_length=20)
    adar_image = models.URLField(max_length=500)
    profile_pic = models.ImageField(upload_to='trainer_profile/', null=True, blank=True)
    experience = models.IntegerField(null=True,blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    password = models.CharField(max_length=128,null=True,blank=True)                          

    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TrainerAvailability(models.Model):
    trainer = models.OneToOneField("trainer.Trainer", on_delete=models.CASCADE)

    mon = models.BooleanField(default=True)
    tue = models.BooleanField(default=True)
    wed = models.BooleanField(default=True)
    thu = models.BooleanField(default=True)
    fri = models.BooleanField(default=True)
    sat = models.BooleanField(default=True)
    sun = models.BooleanField(default=False)

    start_time = models.TimeField(default=time(9, 0))
    end_time = models.TimeField(default=time(18, 0))

    def __str__(self):
        return f"{self.trainer.name} availability"


# class SlotBooking(models.Model):
#     trainer = models.ForeignKey("trainer.Trainer", on_delete=models.CASCADE)
#     client = models.ForeignKey(Client, on_delete=models.CASCADE)
#     plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
#     date = models.DateField()
#     time = models.TimeField()
#     session_end_date = models.DateField(null=True, blank=True)  # when timer finishes
#     session_end_time = models.TimeField(null=True, blank=True)
#     session_start_apihit_time = models.DateTimeField(null=True, blank=True)
#     status = models.CharField(
#         max_length=20,
#         choices=(
#             ('upcoming', 'Upcoming'),
#             ('ongoing', 'Ongoing'),
#             ('completed', 'Completed'),
#             ('missed', 'Missed'),
#             ('cancelled', 'Cancelled')
#         ),
#         default='upcoming'
#     )
#     notes = models.JSONField(default=list, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.trainer.name} - {self.date} {self.time}"
    



class SlotBooking(models.Model):
    BOOKING_TYPE_CHOICES = (
        ('single', 'Single'),
        ('couple', 'Couple'),
        ('group', 'Group'),
    )

    trainer = models.ForeignKey("trainer.Trainer", on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)

    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES,null=True,blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)

    payment = models.ForeignKey(
        "Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="slot_bookings"
    )

    date = models.DateField()
    time = models.TimeField()

    session_end_date = models.DateField(null=True, blank=True)
    session_end_time = models.TimeField(null=True, blank=True)
    session_start_apihit_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=(
            ('upcoming', 'Upcoming'),
            ('ongoing', 'Ongoing'),
            ('completed', 'Completed'),
            ('missed', 'Missed'),
            ('cancelled', 'Cancelled')
        ),
        default='upcoming'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed')
        ),
        default='paid'
    )

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trainer.name} - {self.date} {self.time}"

class Payment(models.Model):
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    trainer = models.ForeignKey("trainer.Trainer", on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)

    booking_type = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    razorpay_order_id = models.CharField(max_length=200)
    razorpay_payment_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=500, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created'
    )

    created_at = models.DateTimeField(auto_now_add=True)


from django.utils import timezone

class TrainerPayment(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('hold', 'Hold'),
    )

    MONTH_CHOICES = (
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    )

    trainer = models.ForeignKey(
        "trainer.Trainer",
        on_delete=models.CASCADE,
        related_name="payments"
    )

    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(choices=MONTH_CHOICES)

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Editable salary (auto-filled from trainer)"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    paid_date = models.DateField(null=True, blank=True)

    approved_date = models.DateField(null=True, blank=True)

    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trainer', 'year', 'month')
        ordering = ['-year', '-month']

    def save(self, *args, **kwargs):
        # 🔹 Auto-fill salary from Trainer if not set
        if not self.salary:
            self.salary = self.trainer.expecting_salary

        # 🔹 Auto set paid_date when status changes to PAID
        if self.status == 'paid' and not self.paid_date:
            self.paid_date = timezone.now().date()

        # 🔹 Clear paid_date if reverted back
        if self.status != 'paid':
            self.paid_date = None

        super().save(*args, **kwargs)




    def __str__(self):
        return f"{self.trainer.name} - {self.month}/{self.year} - {self.status}"

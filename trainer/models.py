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
    expecting_salary = models.DecimalField(max_digits=10, decimal_places=2)
    no_of_section = models.PositiveIntegerField()

    certificates = models.ManyToManyField(TrainerCertificate, blank=True)
    adar_number = models.CharField(max_length=20)
    adar_image = models.URLField(max_length=500)
    profile_pic = models.ImageField(upload_to='trainer_profile/', null=True, blank=True)
    experience = models.IntegerField(null=True,blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    password = models.CharField(max_length=128,null=True,blank=True)  # store trainer-set password temporarily

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


class SlotBooking(models.Model):
    trainer = models.ForeignKey("trainer.Trainer", on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    session_end_date = models.DateField(null=True, blank=True)  # when timer finishes
    session_end_time = models.TimeField(null=True, blank=True)
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
    notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trainer.name} - {self.date} {self.time}"

from django.db import models
from django.contrib.auth import get_user_model

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
    training_field = models.CharField(max_length=100)
    section_timing = models.CharField(max_length=5, choices=SECTION_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    location = models.CharField(max_length=200)
    expecting_salary = models.DecimalField(max_digits=10, decimal_places=2)
    no_of_section = models.PositiveIntegerField()

    certificates = models.ManyToManyField(TrainerCertificate, blank=True)
    adar_number = models.CharField(max_length=20)
    adar_image = models.URLField(max_length=500)
    profile_pic = models.ImageField(upload_to='trainer_profile/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    password = models.CharField(max_length=128,null=True,blank=True)  # store trainer-set password temporarily

    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

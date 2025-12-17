from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Client(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-')
    )

    name = models.CharField(max_length=200)
    phno = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    dob = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    height = models.DecimalField(max_digits=5, decimal_places=2)
    address = models.TextField()
    profile_pic = models.ImageField(upload_to='clients/', null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True)
    health_issues = models.JSONField(default=list, blank=True)
    wellness_goal = models.JSONField(default=list, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

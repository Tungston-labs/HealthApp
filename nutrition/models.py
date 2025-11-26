# models.py
from django.db import models
from client.models import Client  

class NutritionRequest(models.Model):
    CONSULTATION_CHOICES = (
        ("pdf", "PDF / Brochure"),
        ("call", "Call Session"),
        ("email", "Email Consultation"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("closed", "Closed"),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_CHOICES)
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nutrition Request - {self.client.full_name}"

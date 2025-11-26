# tickets/models.py
from django.db import models
from client.models import Client
from trainer.models import Trainer
from plan.models import Plan   # adjust if your app name differs

class Ticket(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("closed", "Closed"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tickets")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name="tickets")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)

    complaint = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.client.name}"

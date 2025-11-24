from django.db import models
from client.models import Client
from trainer.models import Trainer

class TrainerReview(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reviews')
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()  # 1-5 stars
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'trainer')  # prevent multiple reviews per trainer

    def __str__(self):
        return f"{self.client.user.email} → {self.trainer.name} ({self.rating})"

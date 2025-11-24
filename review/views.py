from rest_framework import generics, permissions, serializers
from .models import TrainerReview
from .serializers import TrainerReviewSerializer
from client.models import Client
from accounts.permissions import IsUser

class TrainerReviewCreateView(generics.CreateAPIView):
    serializer_class = TrainerReviewSerializer
    permission_classes = [IsUser]

    def perform_create(self, serializer):
        user = self.request.user
        client = Client.objects.get(user=user)
        trainer_id = self.request.data.get('trainer')

        # Prevent multiple reviews for the same trainer
        if TrainerReview.objects.filter(client=client, trainer_id=trainer_id).exists():
            raise serializers.ValidationError("You have already reviewed this trainer.")

        serializer.save(client=client, trainer_id=trainer_id)

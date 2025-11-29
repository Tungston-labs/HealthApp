from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response

from .models import TrainerReview
from .serializers import TrainerReviewSerializer
from client.models import Client
from accounts.permissions import IsUser


class TrainerReviewCreateView(generics.CreateAPIView):
    serializer_class = TrainerReviewSerializer
    permission_classes = [IsUser]

    def perform_create(self, serializer):
        user = self.request.user
        
        try:
            client = Client.objects.get(user=user)
        except Client.DoesNotExist:
            raise serializers.ValidationError("Client profile not found.")

        trainer_id = self.request.data.get('trainer')
        if not trainer_id:
            raise serializers.ValidationError("Trainer ID is required.")

        # Prevent duplicate review
        if TrainerReview.objects.filter(client=client, trainer_id=trainer_id).exists():
            raise serializers.ValidationError("You have already reviewed this trainer.")

        serializer.save(client=client, trainer_id=trainer_id)

from rest_framework import serializers
from .models import TrainerReview

class TrainerReviewSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.user.name", read_only=True)
    client_profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = TrainerReview
        fields = ["rating", "review", "client_name", "client_profile_pic", "created_at"]

    def get_client_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.client.profile_pic:
            return request.build_absolute_uri(obj.client.profile_pic.url)
        return None

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

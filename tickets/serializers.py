from rest_framework import serializers
from .models import Ticket
from client.models import Client
from nutrition.serializers import ClientDetailSerializer
from trainer.models import Trainer,SlotBooking


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "complaint"]  # Only frontend sends complaint
        read_only_fields = ["id", "status"]

    def create(self, validated_data):
        request = self.context["request"]
        client = request.user.client

        # Get latest active booking for this client
        booking = SlotBooking.objects.filter(client=client, status="upcoming").last()
        if not booking:
            raise serializers.ValidationError("No active booking found for this client.")

        validated_data["client"] = client
        validated_data["trainer"] = booking.trainer
        validated_data["plan"] = booking.plan
        validated_data["status"] = "open"

        return super().create(validated_data)


class TicketListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    client_email = serializers.EmailField(source="client.email", read_only=True)
    client_phone = serializers.CharField(source="client.phno", read_only=True)
    client_profile_pic = serializers.ImageField(source="client.profile_pic", read_only=True)

    plan_name = serializers.CharField(source="plan.plan_name", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "client_name",
            "client_email",
            "client_phone",
            "client_profile_pic",
            "plan",        # plan id
            "plan_name",   # 👈 plan name
            "date",
            "status",
            "complaint"

        ]

class TrainerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = ["name", "email", "phno", "location", "training_field", "profile_pic"]

class TicketDetailSerializer(serializers.ModelSerializer):
    client = ClientDetailSerializer(read_only=True)
    trainer = TrainerDetailSerializer(read_only=True)
    plan_name = serializers.CharField(source="plan.plan_name", read_only=True)


    class Meta:
        model = Ticket
        fields = [
            "id",
            "client",
            "trainer",
            "plan",
            "complaint",
            "status",
            "date",
            "plan_name",
        ]

class TicketStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["status"]

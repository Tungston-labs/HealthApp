from rest_framework import serializers
from .models import NutritionRequest
from client.models import Client
from rest_framework.serializers import SerializerMethodField


class ClientDetailSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = Client
        exclude = ["user"]  # hide sensitive fields

    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None


class NutritionRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NutritionRequest
        fields = ["id", "consultation_type", "note"] 
        read_only_fields = ["id", "status"]

    def create(self, validated_data):
        request = self.context["request"]

        # auto map logged-in client
        validated_data["client"] = request.user.client
        validated_data["status"] = "pending"
        return super().create(validated_data)

from rest_framework import serializers
from trainer.models import SlotBooking   # adjust import path

class NutritionRequestListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    client_email = serializers.EmailField(source="client.email", read_only=True)
    client_phone = serializers.CharField(source="client.phno", read_only=True)
    client_profile_pic = serializers.SerializerMethodField()

    # ✅ PLAN NAME
    plan_name = serializers.SerializerMethodField()

    class Meta:
        model = NutritionRequest
        fields = [
            "id",
            "client_name",
            "client_email",
            "client_phone",
            "client_profile_pic",
            "plan_name",
            "consultation_type",
            "date",
            "status",
        ]

    def get_client_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.client.profile_pic:
            return request.build_absolute_uri(obj.client.profile_pic.url)
        return None

    def get_plan_name(self, obj):
        booking = (
            SlotBooking.objects
            .filter(client=obj.client)
            .select_related("plan")
            .order_by("-created_at")
            .first()
        )
        return booking.plan.plan_name if booking else None


class NutritionRequestDetailSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()

    class Meta:
        model = NutritionRequest
        fields = [
            "id",
            "client",
            "plan_name",
            "consultation_type",
            "note",
            "date",
            "status",
        ]

    def get_client(self, obj):
        return ClientDetailSerializer(
            obj.client,
            context=self.context
        ).data

    def get_plan_name(self, obj):
        booking = (
            SlotBooking.objects
            .filter(client=obj.client)
            .select_related("plan")
            .order_by("-created_at")
            .first()
        )
        return booking.plan.plan_name if booking else None


from rest_framework import serializers
from django.db import transaction
from .models import TrainingCancelRequest
from trainer.models import SlotBooking


class TrainingCancelRequestSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)
    plan_name = serializers.CharField(source="plan.plan_name", read_only=True)

    class Meta:
        model = TrainingCancelRequest
        fields = [
            "id",
            "trainer_name",
            "client_name",
            "plan_name",
            "amount",
            "status",
            "request_date",
            "reason",
        ]


class TrainingCancelListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name")
    trainer_name = serializers.CharField(source="trainer.name")
    training_field = serializers.CharField(source="trainer.training_field")
    plan_name = serializers.CharField(source="plan.name", default=None)

    class Meta:
        model = TrainingCancelRequest
        fields = [
            "id",
            "client_name",
            "trainer_name",
            "training_field",
            "plan_name",
            "amount",
            "request_date",
            "status",
        ]


class TrainingCancelDetailSerializer(serializers.ModelSerializer):
    # Client
    client_name = serializers.CharField(source="client.name")
    client_email = serializers.CharField(source="client.email")
    client_phone = serializers.CharField(source="client.phno")

    # Trainer
    trainer_name = serializers.CharField(source="trainer.name")
    training_field = serializers.CharField(
        source="trainer.training_field.plan_name",
        default=None
    )

    # Plan
    plan_name = serializers.CharField(
        source="plan.plan_name",
        default=None
    )

    # SlotBooking
    session_date = serializers.DateField(source="slot.date")
    session_time = serializers.TimeField(source="slot.time")
    session_end_date = serializers.DateField(source="slot.session_end_date")
    session_end_time = serializers.TimeField(source="slot.session_end_time")

    class Meta:
        model = TrainingCancelRequest
        fields = [
            "id",
            "client_name",
            "client_email",
            "client_phone",
            "trainer_name",
            "training_field",
            "plan_name",
            "session_date",
            "session_time",
            "session_end_date",
            "session_end_time",
            "amount",
            "reason",
            "request_date",
            "status",
        ]


class TrainingCancelStatusUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TrainingCancelRequest
        fields = ["status"]

    def update(self, instance, validated_data):
        with transaction.atomic():
            old_status = instance.status
            new_status = validated_data.get("status")

            instance.status = new_status
            instance.save()

            if new_status in ["approved", "closed"] and old_status != new_status:
                slot = getattr(instance, "slot", None)
                if slot is not None:
                    slot.status = "cancelled"
                    slot.save(update_fields=["status"])
                else:
                    slot_id = instance.slot_id
                    if slot_id:
                        SlotBooking.objects.filter(id=slot_id).update(status="cancelled")

        return instance

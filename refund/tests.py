from django.test import TestCase
from django.contrib.auth import get_user_model

from client.models import Client
from plan.models import Plan
from trainer.models import SlotBooking, Trainer
from .models import TrainingCancelRequest
from .serializers import TrainingCancelStatusUpdateSerializer


class TrainingCancelStatusUpdateSerializerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="secret123",
            phno="5551234567",
            name="Test User",
            role="user",
        )

        self.client = Client.objects.create(
            name="Test Client",
            phno="1234567890",
            email="client@example.com",
            dob="2000-01-01",
            gender="male",
            blood_group="A+",
            weight=70,
            height=170,
            address="Test address",
            user=self.user,
        )

        self.plan = Plan.objects.create(
            plan_name="Test Plan",
            plan_type="3_days",
            single_price=100,
            couple_price=200,
            group_price=300,
            description="Test plan",
        )

        self.trainer = Trainer.objects.create(
            name="Test Trainer",
            phno="0987654321",
            email="trainer@example.com",
            dob="1990-01-01",
            training_field=self.plan,
            section_timing="30",
            gender="male",
            location="Test location",
            expecting_salary=1000,
            no_of_section=1,
            adar_number="123456789012",
            adar_image="https://example.com/adhar.jpg",
        )

        self.slot = SlotBooking.objects.create(
            trainer=self.trainer,
            client=self.client,
            plan=self.plan,
            booking_type="single",
            amount_paid=100,
            date="2026-07-02",
            time="10:00:00",
            status="upcoming",
            payment_status="paid",
        )

        self.cancel_request = TrainingCancelRequest.objects.create(
            client=self.client,
            trainer=self.trainer,
            plan=self.plan,
            slot=self.slot,
            amount=100,
            status="open",
        )

    def test_closed_status_cancels_the_related_slot(self):
        serializer = TrainingCancelStatusUpdateSerializer(
            self.cancel_request,
            data={"status": "closed"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, "cancelled")

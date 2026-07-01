from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from client.models import Client
from plan.models import Plan
from trainer.models import SlotBooking, Trainer


class PlanListViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="client-plan@example.com",
            password="secret123",
            phno="1234567890",
            name="Client User",
            role="user",
        )

        self.client = Client.objects.create(
            name="Test Client",
            phno="1234567890",
            email="client-plan@example.com",
            dob="2000-01-01",
            gender="male",
            blood_group="A+",
            weight=70,
            height=170,
            address="Test address",
            user=self.user,
        )

        self.plan = Plan.objects.create(
            plan_name="Removed Trainer Plan",
            plan_type="3_days",
            single_price=100,
            couple_price=200,
            group_price=300,
            description="Test plan",
        )

        self.trainer = Trainer.objects.create(
            name="Removed Trainer",
            phno="0987654321",
            email="removed-trainer@example.com",
            dob="1990-01-01",
            training_field=self.plan,
            section_timing="30",
            gender="male",
            location="Test location",
            expecting_salary=1000,
            no_of_section=1,
            adar_number="123456789012",
            adar_image="https://example.com/adhar.jpg",
            status="rejected",
        )

        SlotBooking.objects.create(
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

        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)

    def test_plan_is_listed_when_booking_is_no_longer_active_due_to_removed_trainer(self):
        response = self.api_client.get("/api/plan/clientlist/")

        self.assertEqual(response.status_code, 200)
        data = response.json().get("data", [])
        self.assertTrue(any(plan["id"] == self.plan.id for plan in data))

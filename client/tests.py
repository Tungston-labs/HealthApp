from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from rest_framework import serializers
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from health.upload_fields import ImageUploadField
from client.models import Client
from plan.models import Plan
from trainer.models import Trainer, SlotBooking


class ImageUploadFieldTests(SimpleTestCase):
    class UploadSerializer(serializers.Serializer):
        image = ImageUploadField()

    def test_accepts_heic_and_webp_extensions(self):
        for filename in ("profile.heic", "banner.webp"):
            serializer = self.UploadSerializer(
                data={
                    "image": SimpleUploadedFile(
                        filename,
                        b"image-bytes",
                        content_type="application/octet-stream",
                    )
                }
            )

            self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_unsupported_extensions(self):
        serializer = self.UploadSerializer(
            data={
                "image": SimpleUploadedFile(
                    "profile.pdf",
                    b"pdf-bytes",
                    content_type="application/pdf",
                )
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("image", serializer.errors)


class UnBookedPlanListViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="client@example.com",
            password="secret123",
            phno="1234567890",
            name="Client User",
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
            status="cancelled",
            payment_status="paid",
        )

        self.api_client = APIClient()
        self.api_client.force_authenticate(user=self.user)

    def test_cancelled_training_plan_is_returned_as_unbooked(self):
        response = self.api_client.get("/api/client/plans/unbooked/")

        self.assertEqual(response.status_code, 200)
        data = response.json().get("data", [])
        self.assertTrue(any(plan["id"] == self.plan.id for plan in data))

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

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

        self.plan2 = Plan.objects.create(
            plan_name="Other Plan",
            plan_type="6_days",
            single_price=150,
            couple_price=250,
            group_price=350,
            description="Another plan",
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

        self.slot2 = SlotBooking.objects.create(
            trainer=self.trainer,
            client=self.client,
            plan=self.plan,
            booking_type="single",
            amount_paid=150,
            date="2026-07-03",
            time="11:00:00",
            status="ongoing",
            payment_status="paid",
        )

        self.trainer2 = Trainer.objects.create(
            name="Other Trainer",
            phno="1111111111",
            email="othertrainer@example.com",
            dob="1991-01-01",
            training_field=self.plan2,
            section_timing="30",
            gender="male",
            location="Other location",
            expecting_salary=1200,
            no_of_section=1,
            adar_number="222222222222",
            adar_image="https://example.com/adhar2.jpg",
        )

        self.other_slot = SlotBooking.objects.create(
            trainer=self.trainer2,
            client=self.client,
            plan=self.plan2,
            booking_type="single",
            amount_paid=200,
            date="2026-07-04",
            time="12:00:00",
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
        self.slot2.refresh_from_db()
        self.other_slot.refresh_from_db()

        self.assertEqual(self.slot.status, "cancelled")
        self.assertEqual(self.slot2.status, "cancelled")
        self.assertEqual(self.other_slot.status, "upcoming")


class TrainerDisappearsAfterCancellationTests(APITestCase):
    """Test that trainer disappears from booked trainers after admin closes a cancellation request"""
    
    def setUp(self):
        # Create user
        self.user = get_user_model().objects.create_user(
            email="client@example.com",
            password="password123",
            phno="5551234567",
            name="Test Client",
            role="user",
        )
        
        # Create client
        self.client_obj = Client.objects.create(
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
        
        # Create admin user
        self.admin_user = get_user_model().objects.create_user(
            email="admin@example.com",
            password="admin123",
            phno="9999999999",
            name="Admin",
            role="admin",
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()
        
        # Create plan
        self.plan = Plan.objects.create(
            plan_name="Yoga",
            plan_type="3_days",
            single_price=100,
            couple_price=200,
            group_price=300,
            description="Yoga plan",
        )
        
        # Create trainer
        self.trainer = Trainer.objects.create(
            name="Kavya",
            phno="0987654321",
            email="trainer@example.com",
            dob="1990-01-01",
            training_field=self.plan,
            section_timing="30",
            gender="female",
            location="Test location",
            expecting_salary=1000,
            no_of_section=1,
            adar_number="123456789012",
            adar_image="https://example.com/adhar.jpg",
        )
        
        # Create slot booking
        self.slot = SlotBooking.objects.create(
            trainer=self.trainer,
            client=self.client_obj,
            plan=self.plan,
            booking_type="single",
            amount_paid=100,
            date="2026-07-15",
            time="09:00:00",
            status="upcoming",
            payment_status="paid",
        )
        
        # Create token for client
        refresh = RefreshToken.for_user(self.user)
        self.client_token = str(refresh.access_token)
        
        # Create token for admin
        refresh_admin = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(refresh_admin.access_token)
    
    def test_trainer_disappears_after_cancellation_closed(self):
        """Verify that trainer is removed from booked trainers list when cancellation is closed"""
        
        # 1. Verify trainer is in booked trainers list
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.client_token}")
        response = self.client.get("/api/client/booked-trainers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["data"][0]["trainer_name"], "Kavya")
        self.assertEqual(response.data["data"][0]["id"], self.slot.id)
        
        # 2. Create cancellation request
        response = self.client.post(
            "/api/refund/training/cancel/",
            {"slot_id": self.slot.id},
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        cancel_request_id = response.data["data"]["request_id"]
        
        # 3. Admin closes the cancellation request
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.patch(
            f"/api/refund/cancel-requests/{cancel_request_id}/status/",
            {"status": "closed"},
            format="json"
        )
        self.assertEqual(response.status_code, 200)
        
        # 4. Verify slot is now cancelled
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, "cancelled")
        
        # 5. Verify trainer is no longer in booked trainers list
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.client_token}")
        response = self.client.get("/api/client/booked-trainers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_trainer_id_request_cancels_all_active_bookings_for_that_trainer(self):
        """Verify that trainer_id-based cancellation removes the trainer from the booked list."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.client_token}")
        response = self.client.post(
            "/api/refund/training/cancel/",
            {"trainer_id": self.trainer.id},
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        cancel_request_id = response.data["data"]["request_id"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.patch(
            f"/api/refund/cancel-requests/{cancel_request_id}/status/",
            {"status": "closed"},
            format="json"
        )
        self.assertEqual(response.status_code, 200)

        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, "cancelled")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.client_token}")
        response = self.client.get("/api/client/booked-trainers/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

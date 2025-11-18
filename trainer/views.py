# accounts/views.py
from rest_framework import generics, permissions,status
from rest_framework.views import APIView
from django.core.files.storage import default_storage
from django.conf import settings
import os
from .serializers import TrainerSerializer
from rest_framework.response import Response
from .models import Trainer
from accounts.models import User  # your custom User model
from accounts.permissions import IsAdmin,IsTrainer,IsAdminOrTrainer,IsUser


class LocalImageUploadAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided"}, status=400)

        path = default_storage.save(f"certificates/{file.name}", file)

        # ✅ Correct: use full path
        url = request.build_absolute_uri(settings.MEDIA_URL + path)

        return Response({"url": url}, status=200)



class TrainerCreateView(generics.CreateAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [permissions.AllowAny]


class TrainerListView(generics.ListAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        trainer = self.get_object()
        old_status = trainer.status
        serializer = self.get_serializer(trainer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data.get('status', old_status)

        # Pending -> Rejected
        if old_status == 'pending' and new_status == 'rejected':
            trainer.delete()
            return Response({"detail": "Trainer rejected and deleted"}, status=200)

        # Approved -> Rejected
        if old_status == 'approved' and new_status == 'rejected':
            if trainer.user:
                trainer.user.delete()
            trainer.delete()
            return Response({"detail": "Trainer rejected and deleted along with user"}, status=200)

        # Update trainer normally
        serializer.save()

        # Pending -> Approved or any -> Approved
        if new_status == 'approved' and trainer.user is None:
            user = User.objects.create_user(
                email=trainer.email,
                password=trainer.password,
                role='trainer',
                name=trainer.name,
                phno=trainer.phno
            )
            trainer.user = user
            trainer.save()

        return Response(serializer.data)


class PendingTrainerListView(generics.ListAPIView):
    """
    API view to list all trainers whose status is 'pending'
    """
    serializer_class = TrainerSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users (Admin/Trainer)

    def get_queryset(self):
        return Trainer.objects.filter(status='pending').order_by('-created_at')


# ===============================  MOBILE APP  ===============================

class TrainerProfileView(generics.RetrieveAPIView):
    serializer_class = TrainerSerializer
    permission_classes = [IsTrainer]

    def get_object(self):
        # Return the trainer associated with logged-in user
        return Trainer.objects.get(user=self.request.user)


class TrainerProfileEditView(generics.UpdateAPIView):
    serializer_class = TrainerSerializer
    permission_classes = [IsTrainer]

    def get_object(self):
        return Trainer.objects.get(user=self.request.user)

from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.db.models import Q

from .models import Trainer, TrainerAvailability, SlotBooking
from .serializers import TrainerSerializer
from plan.models import Plan
from client.models import Client

class FilterTrainersView(APIView):
    permission_classes = [IsUser]

    def post(self, request):

        plan_id = request.data.get("plan_id")
        slot_days = request.data.get("slot_days")      # ["mon", "wed"]
        time_slot = request.data.get("time")           # "10:00"
        start_date = request.data.get("start_date")    # "2025-02-01"

        # Validate input
        if not (plan_id and slot_days and time_slot and start_date):
            return Response({"error": "Missing fields"}, 400)

        # Get Client
        try:
            client = Client.objects.get(user=request.user)
        except:
            return Response({"error": "Client not found"}, 400)

        client_gender = client.gender.lower()

        # Convert time/date
        time_slot_obj = datetime.strptime(time_slot, "%H:%M").time()
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()

        # ------------------------------
        # PLAN DURATION FIX
        # ------------------------------
        plan = Plan.objects.get(id=plan_id)

        if plan.plan_type == "3_days":
            duration = 3
        elif plan.plan_type == "6_days":
            duration = 6
        else:
            duration = 30  # fallback

        end_date = start_date_obj + timedelta(days=duration)

        # Weekday mapping
        weekday_map = {"mon":0,"tue":1,"wed":2,"thu":3,"fri":4,"sat":5,"sun":6}
        slot_days = [d.lower() for d in slot_days]
        wanted_weekdays = [weekday_map[d] for d in slot_days]

        # Generate session dates
        session_dates = []
        d = start_date_obj
        while d <= end_date:
            if d.weekday() in wanted_weekdays:
                session_dates.append(d)
            d += timedelta(days=1)

        # ------------------------------
        # TRAINER FILTER - FIXED
        # ------------------------------
        trainers = Trainer.objects.filter(
            training_field_id=plan_id,
            status__iexact="approved",
            gender__iexact=client_gender
        )

        available = []

        for tr in trainers:

            # Availability check
            try:
                avl = tr.traineravailability
            except TrainerAvailability.DoesNotExist:
                continue

            # Day check
            if not all(getattr(avl, day) for day in slot_days):
                continue

            # Time check
            if not (avl.start_time <= time_slot_obj <= avl.end_time):
                continue

            # Booking conflict check
            conflict = SlotBooking.objects.filter(
                trainer=tr,
                date__in=session_dates,
                time=time_slot_obj
            ).exists()

            if conflict:
                continue

            available.append(tr)

        return Response({
            "plan_id": plan_id,
            "total_available": len(available),
            "available_trainers": TrainerSerializer(available, many=True).data
        })


from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timedelta
from .models import Trainer, TrainerAvailability, SlotBooking
from plan.models import Plan
from client.models import Client

class BookTrainerView(APIView):
    permission_classes = [IsUser]


    def post(self, request):
        trainer_id = request.data.get("trainer_id")
        plan_id = request.data.get("plan_id")
        start_date = request.data.get("start_date")
        time_slot = request.data.get("time")  # "10:00"
        slot_days = request.data.get("slot_days")  # optional for non-gym

        if not (trainer_id and plan_id and start_date and time_slot):
            return Response({"error": "Missing required fields"}, status=400)

        # Get client
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Client profile not found"}, status=400)

        # Convert inputs
        time_slot_obj = datetime.strptime(time_slot, "%H:%M").time()
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        trainer = Trainer.objects.get(id=trainer_id, status="approved")
        plan = Plan.objects.get(id=plan_id)

        # Duration = 30 days
        duration = 30
        end_date = start_date_obj + timedelta(days=duration)

        # Determine weekdays
        weekday_map = {
            "mon": 0, "tue": 1, "wed": 2,
            "thu": 3, "fri": 4, "sat": 5
        }

        # If Gym plan, ignore frontend days → use Mon-Sat automatically
        if plan.plan_type == "6_days":
            slot_days = ["mon","tue","wed","thu","fri","sat"]

        selected_weekdays = [weekday_map[d] for d in slot_days]

        # Generate all session dates
        session_dates = []
        current = start_date_obj
        while current <= end_date:
            if current.weekday() in selected_weekdays:
                session_dates.append(current)
            current += timedelta(days=1)

        # Check trainer availability
        availability = TrainerAvailability.objects.filter(trainer=trainer).first()
        if not availability:
            return Response({"error": "Trainer availability not found"}, status=400)

        # Weekly check
        for day in slot_days:
            if not getattr(availability, day):
                return Response({"error": f"Trainer not available on {day}"}, status=400)

        # Time check
        if not (availability.start_time <= time_slot_obj <= availability.end_time):
            return Response({"error": "Trainer not available at selected time"}, status=400)

        # Check conflicts
        conflicts = SlotBooking.objects.filter(
            trainer=trainer,
            date__in=session_dates,
            time=time_slot_obj
        ).exists()

        if conflicts:
            return Response({"error": "Trainer already booked for some of the selected dates"}, status=400)

        # ✅ All good → create SlotBooking for all dates
        bookings = []
        for date in session_dates:
            booking = SlotBooking.objects.create(
                trainer=trainer,
                client=client,
                plan=plan,
                date=date,
                time=time_slot_obj
            )
            bookings.append(booking)

        return Response({
            "message": "Trainer booked successfully",
            "total_sessions": len(bookings),
            "start_date": start_date,
            "end_date": end_date,
            "trainer_id": trainer.id
        })

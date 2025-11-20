# accounts/views.py
from rest_framework import generics, permissions,status
from rest_framework.views import APIView
from django.core.files.storage import default_storage
from django.conf import settings
import os
from .serializers import TrainerSerializer
from accounts.models import User  # your custom User model
from accounts.permissions import IsAdmin,IsTrainer,IsAdminOrTrainer,IsUser
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.db.models import Q

from .models import Trainer, TrainerAvailability, SlotBooking
from plan.models import Plan
from client.models import Client


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



class FilterTrainersView(APIView):
    permission_classes = [IsUser]

    def post(self, request):

        plan_id = request.data.get("plan_id")
        slot_days = request.data.get("slot_days")
        time_slot = request.data.get("time")
        start_date = request.data.get("start_date")

        if not (plan_id and slot_days and time_slot and start_date):
            return Response({"error": "Missing fields"}, 400)

        # get client
        client = Client.objects.get(user=request.user)
        client_gender = client.gender.lower()

        # parse inputs
        time_slot_obj = datetime.strptime(time_slot, "%H:%M").time()
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()

        # plan mapping
        plan = Plan.objects.get(id=plan_id)
        plan_type_map = {"3_days": 3, "6_days": 6}
        duration = plan_type_map.get(plan.plan_type, 30)
        end_date = start_date_obj + timedelta(days=duration)

        # weekday mapping
        weekday_map = {"mon":0,"tue":1,"wed":2,"thu":3,"fri":4,"sat":5}
        slot_days = [d.lower() for d in slot_days]
        wanted_weekdays = [weekday_map[d] for d in slot_days]

        # filter trainers
        trainers = Trainer.objects.filter(
            training_field_id=plan_id,
            status__iexact="approved",
            gender__iexact=client_gender
        )

        available = []

        for tr in trainers:

            # availability
            try:
                avl = tr.traineravailability
            except:
                continue

            # weekly day check
            if not all(getattr(avl, day) for day in slot_days):
                continue

            # time check
            if not (avl.start_time <= time_slot_obj <= avl.end_time):
                continue

            # ----------------------------------------------------
            # NEW SESSION DATES: fill only up to tr.no_of_section
            # ----------------------------------------------------
            max_sessions = tr.no_of_section
            session_dates = []

            d = start_date_obj
            filled = 0

            while filled < max_sessions:
                if d.weekday() in wanted_weekdays:
                    session_dates.append(d)
                    filled += 1
                    if filled >= max_sessions:
                        break
                d += timedelta(days=1)

            # booking conflict
            conflict = SlotBooking.objects.filter(
                trainer=tr,
                date__in=session_dates,
                time=time_slot_obj
            ).exists()

            if conflict:
                continue

            available.append(tr)

        return Response({
            "plan": {
                "id": plan.id,
                "name": plan.plan_name,
                "plan_type": plan.plan_type,
                "single_price": plan.single_price,
                "couple_price": plan.couple_price,
                "group_price": plan.group_price,
            },
            "client_address": client.address,   # 👈 NEW — logged-in user address
            "total_available": len(available),
            "available_trainers": TrainerSerializer(available, many=True).data
        })




class BookTrainerView(APIView):
    permission_classes = [IsUser]

    def post(self, request):
        trainer_id = request.data.get("trainer_id")
        plan_id = request.data.get("plan_id")
        start_date = request.data.get("start_date")
        time_slot = request.data.get("time")
        slot_days = request.data.get("slot_days")

        if not (trainer_id and plan_id and start_date and time_slot):
            return Response({"error": "Missing required fields"}, status=400)

        # Get client
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Client profile not found"}, status=400)

        # Convert
        time_slot_obj = datetime.strptime(time_slot, "%H:%M").time()
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()

        trainer = Trainer.objects.get(id=trainer_id, status="approved")
        plan = Plan.objects.get(id=plan_id)

        # -----------------------------------------
        # PLAN → DURATION
        # -----------------------------------------
        if plan.plan_type == "3_days":
            duration = 3
        elif plan.plan_type == "6_days":
            duration = 6
        else:
            duration = 30

        end_date = start_date_obj + timedelta(days=duration)

        # -----------------------------------------
        # DAY PATTERN FOR 6-DAY GYM PLAN
        # -----------------------------------------
        weekday_map = {"mon":0,"tue":1,"wed":2,"thu":3,"fri":4,"sat":5,"sun":6}

        if plan.plan_type == "6_days":
            slot_days = ["mon","tue","wed","thu","fri","sat"]

        slot_days = [d.lower() for d in slot_days]
        selected_weekdays = [weekday_map[d] for d in slot_days]

        # -----------------------------------------
        # NEW SESSION GENERATION USING no_of_section
        # -----------------------------------------
        max_sessions = trainer.no_of_section  # e.g 10 or 14
        session_dates = []

        d = start_date_obj
        filled = 0

        while filled < max_sessions:
            if d.weekday() in selected_weekdays:
                session_dates.append(d)
                filled += 1
                if filled >= max_sessions:
                    break
            d += timedelta(days=1)

        # -----------------------------------------
        # AVAILABILITY CHECK
        # -----------------------------------------
        availability = TrainerAvailability.objects.filter(trainer=trainer).first()
        if not availability:
            return Response({"error": "Trainer availability not found"}, 400)

        for day in slot_days:
            if not getattr(availability, day):
                return Response({"error": f"Trainer not available on {day}"}, 400)

        if not (availability.start_time <= time_slot_obj <= availability.end_time):
            return Response({"error": "Trainer not available at that time"}, 400)

        # -----------------------------------------
        # CONFLICT CHECK
        # -----------------------------------------
        conflict = SlotBooking.objects.filter(
            trainer=trainer,
            date__in=session_dates,
            time=time_slot_obj
        ).exists()

        if conflict:
            return Response({"error": "Trainer already booked on some session dates"}, 400)

        # -----------------------------------------
        # CREATE BOOKINGS
        # -----------------------------------------
        for date in session_dates:
            SlotBooking.objects.create(
                trainer=trainer,
                client=client,
                plan=plan,
                date=date,
                time=time_slot_obj
            )

        return Response({
            "message": "Trainer booked successfully",
            "total_sessions": len(session_dates),
            "trainer_id": trainer.id,
            "start_date": str(start_date_obj),
            "end_date": str(end_date)
        })

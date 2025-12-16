# accounts/views.py
from rest_framework import generics, permissions,status
from rest_framework.views import APIView
from django.core.files.storage import default_storage
from django.conf import settings
import os
from .serializers import TrainerSerializer,TrainerMiniSerializer,ChangeTrainerSerializer,SlotBookingNoteSerializer
from accounts.models import User  # your custom User model
from accounts.permissions import IsAdmin,IsTrainer,IsAdminOrTrainer,IsUser
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.db.models import Q

from .models import Trainer, TrainerAvailability, SlotBooking
from plan.models import Plan
from client.models import Client
from accounts.paginations import CustomPagination


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


from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend


class TrainerListView(generics.ListAPIView):
    serializer_class = TrainerSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name']
    filterset_fields = ['training_field']

    def get_queryset(self):
        return Trainer.objects.filter(status='approved')


from datetime import time
class TrainerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        trainer = self.get_object()

        # Delete linked user (if exists)
        if trainer.user:
            trainer.user.delete()

        trainer.delete()
        return Response({"detail": "Trainer and related user deleted"}, status=200)



    def patch(self, request, *args, **kwargs):
        trainer = self.get_object()
        old_status = trainer.status

        serializer = self.get_serializer(trainer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data.get('status', old_status)

        # Pending -> Rejected
        if old_status == 'pending' and new_status == 'rejected':
            if trainer.user:
                trainer.user.delete()
            trainer.delete()
            return Response({"detail": "Trainer rejected and deleted"}, status=200)

        # Approved -> Rejected
        if old_status == 'approved' and new_status == 'rejected':
            if trainer.user:
                trainer.user.delete()
            trainer.delete()
            return Response({"detail": "Trainer rejected and deleted along with user"}, status=200)

        # Save trainer changes
        serializer.save()

        # 🚀 CREATE USER + AVAILABILITY ONLY WHEN APPROVED
        if new_status == 'approved' and trainer.user is None:

            # Create user
            user = User.objects.create_user(
                email=trainer.email,
                password=trainer.password,
                role='trainer',
                name=trainer.name,
                phno=trainer.phno
            )
            trainer.user = user
            trainer.save()

            # ✅ CREATE DEFAULT AVAILABILITY
            TrainerAvailability.objects.get_or_create(
                trainer=trainer,
                defaults={
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": False,
                    "start_time": time(9, 0),
                    "end_time": time(18, 0),
                }
            )

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
            "available_trainers": TrainerMiniSerializer(
                available,
                many=True,
                context={"plan": plan,"request":request}
            ).data
        })
# for client to view trainer details in modal includig reviews
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from trainer.models import Trainer
from .serializers import TrainerDetailSerializer

class TrainerDetailPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trainer_id):
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        serializer = TrainerDetailSerializer(
            trainer,
            context={"request": request}  # ★ IMPORTANT FIX
        )
        return Response(serializer.data)




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

class ChangeTrainerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Get client
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Client profile not found"}, 404)

        # 2. Find latest booking (current trainer info)
        latest_booking = SlotBooking.objects.filter(client=client).order_by('-date').first()
        if not latest_booking:
            return Response({"error": "No active bookings found"}, 400)

        current_trainer = latest_booking.trainer
        plan = latest_booking.plan
        time_slot_obj = latest_booking.time
        start_date_obj = latest_booking.date

        # 3. Calculate plan duration
        duration_map = {"3_days": 3, "6_days": 6}
        duration = duration_map.get(plan.plan_type, 30)
        end_date = start_date_obj + timedelta(days=duration)

        # 4. Extract slot days from bookings
        weekday_map_reverse = {0:"mon",1:"tue",2:"wed",3:"thu",4:"fri",5:"sat",6:"sun"}

        all_client_bookings = SlotBooking.objects.filter(
            client=client,
            trainer=current_trainer,
            plan=plan
        )

        slot_days = list({weekday_map_reverse[b.date.weekday()] for b in all_client_bookings})
        wanted_weekdays = [b.date.weekday() for b in all_client_bookings]

        # 5. Get salary threshold
        min_salary = current_trainer.expecting_salary

        # 6. Filter trainers
        trainers = Trainer.objects.filter(
            training_field_id=plan.id,
            status="approved",
            gender=client.gender.lower(),
            expecting_salary__gte=min_salary
        ).exclude(id=current_trainer.id)

        available = []

        for tr in trainers:
            try:
                avl = tr.traineravailability
            except:
                continue

            # check days
            if not all(getattr(avl, d) for d in slot_days):
                continue

            # check time
            if not (avl.start_time <= time_slot_obj <= avl.end_time):
                continue

            # build session dates
            max_sessions = tr.no_of_section
            d = start_date_obj
            session_dates = []
            filled = 0

            while filled < max_sessions:
                if d.weekday() in wanted_weekdays:
                    session_dates.append(d)
                    filled += 1
                d += timedelta(days=1)

            # conflict check
            if SlotBooking.objects.filter(trainer=tr, date__in=session_dates, time=time_slot_obj).exists():
                continue

            available.append(tr)

        serializer = ChangeTrainerSerializer(available, many=True, context={"request": request})

        return Response({
            "total_available": len(available),
            "available_trainers": serializer.data
        })
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from trainer.models import Trainer
from client.models import Client
from .serializers import TrainerInfoSerializer

class TrainerDetailSimpleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trainer_id):
        # trainer
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        # authenticated user client details
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        serializer = TrainerInfoSerializer(
            trainer,
            context={"request": request}
        )

        return Response({
            "trainer": serializer.data,
            "client_address": client.address
        })


class AddSlotBookingNoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = SlotBooking.objects.get(id=booking_id, trainer__user=request.user)
        except SlotBooking.DoesNotExist:
            return Response({"error": "Booking not found or not authorized"}, status=404)

        note = request.data.get("note")
        if not note:
            return Response({"error": "Note is required"}, status=400)

        booking.notes = note
        booking.save()

        serializer = SlotBookingNoteSerializer(booking)
        return Response({"message": "Note added successfully", "booking": serializer.data})

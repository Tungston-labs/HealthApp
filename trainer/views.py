# accounts/views.py
from rest_framework import generics, permissions,status
from rest_framework.views import APIView
from django.core.files.storage import default_storage
from django.conf import settings
import logging
import os
from .serializers import TrainerSerializer,TrainerMiniSerializer,ChangeTrainerSerializer,SlotBookingNoteSerializer
from health.upload_fields import validate_image_extension
from accounts.models import User  # your custom User model
from accounts.permissions import IsAdmin,IsTrainer,IsAdminOrTrainer,IsUser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from datetime import datetime, timedelta
from django.db.models import Q

from .models import Trainer, TrainerAvailability, SlotBooking
from plan.models import Plan
from client.models import Client
from accounts.paginations import CustomPagination

logger = logging.getLogger(__name__)

class LocalImageUploadAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided"}, status=400)

        try:
            validate_image_extension(file)
        except ValidationError as exc:
            return Response({"error": exc.detail}, status=400)

        path = default_storage.save(f"certificates/{file.name}", file)

        # ✅ Correct: use full path
        url = request.build_absolute_uri(settings.MEDIA_URL + path)

        return Response({"url": url}, status=200)



from rest_framework.parsers import MultiPartParser, FormParser

class TrainerCreateView(generics.CreateAPIView):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Trainer serializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=400)

        return super().create(request, *args, **kwargs)


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
        return Trainer.objects.filter(
            status='approved',
            user__is_active=True
        )
class TrainerPendingListView(generics.ListAPIView):
    serializer_class = TrainerSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Trainer.objects.filter(
            status='pending'
        )

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
    serializer_class = TrainerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        plan_id = self.kwargs.get("plan_id")

        return Trainer.objects.filter(
            status="pending",
            training_field_id=plan_id
        ).order_by("-created_at")

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
    parser_classes = [MultiPartParser,FormParser]

    def get_object(self):
        return Trainer.objects.get(user=self.request.user)


from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Trainer, TrainerAvailability, SlotBooking, Plan, Client
from .serializers import TrainerMiniSerializer


class FilterTrainersView(APIView):
    permission_classes = [IsUser]

    def haversine(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two lat/lng points in KM"""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371
        return c * r

    def post(self, request):
        plan_id = request.data.get("plan_id")
        slot_days = request.data.get("slot_days")      # ["mon", "wed"]
        time_slot = request.data.get("time")           # "06:00"
        start_date = request.data.get("start_date")    # "2026-01-10"

        logger.debug(
            "FilterTrainersView request body: plan_id=%s slot_days=%s time=%s start_date=%s",
            plan_id,
            slot_days,
            time_slot,
            start_date,
        )

        # ---------------- VALIDATION ----------------
        if not plan_id or not slot_days or not time_slot or not start_date:
            return Response(
                {"status": False, "message": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------- CLIENT ----------------
        client = get_object_or_404(Client, user=request.user)

        if not client.latitude or not client.longitude:
            return Response(
                {"status": False, "message": "Client location not set"},
                status=status.HTTP_400_BAD_REQUEST
            )

        client_gender = client.gender.lower()
        client_lat = client.latitude
        client_lon = client.longitude

        # ---------------- PARSE DATE & TIME ----------------
        try:
            time_slot_obj = datetime.strptime(time_slot, "%H:%M").time()
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"status": False, "message": "Invalid date or time format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------- PLAN ----------------
        plan = get_object_or_404(Plan, id=plan_id)

        plan_duration_map = {
            "3_days": 3,
            "6_days": 6
        }
        duration = plan_duration_map.get(plan.plan_type, 30)
        end_date = start_date_obj + timedelta(days=duration)

        # ---------------- WEEKDAYS ----------------
        weekday_map = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6
        }

        slot_days = [d.lower() for d in slot_days]
        wanted_weekdays = [weekday_map[d] for d in slot_days if d in weekday_map]

        # ---------------- BASE TRAINERS ----------------
        base_trainers = Trainer.objects.filter(
            training_field_id=plan_id,
            status__iexact="approved",
            gender__iexact=client_gender
        )

        matched_trainers = []

        # ---------------- FILTER LOGIC ----------------
        for trainer in base_trainers:

            # -------- LOCATION CHECK --------
            if trainer.latitude is None or trainer.longitude is None:
                continue

            distance = self.haversine(
                client_lat,
                client_lon,
                trainer.latitude,
                trainer.longitude
            )

            if distance > 5:
                continue

            # -------- AVAILABILITY --------
            try:
                availability = trainer.traineravailability
            except TrainerAvailability.DoesNotExist:
                continue

            if not all(getattr(availability, day) for day in slot_days):
                continue

            # -------- TIME CHECK --------
            if not (availability.start_time <= time_slot_obj <= availability.end_time):
                continue

            # -------- SESSION DATE GENERATION --------
            max_sessions = trainer.no_of_section
            session_dates = []
            d = start_date_obj

            while len(session_dates) < max_sessions and d <= end_date:
                if d.weekday() in wanted_weekdays:
                    session_dates.append(d)
                d += timedelta(days=1)

            # -------- BOOKING CONFLICT --------
            conflict = SlotBooking.objects.filter(
                trainer=trainer,
                date__in=session_dates,
                time=time_slot_obj
            ).exists()

            if conflict:
                continue

            matched_trainers.append(trainer)

        # ---------------- REMAINING TRAINERS ----------------
        matched_ids = [t.id for t in matched_trainers]

        other_trainers = base_trainers.exclude(id__in=matched_ids)

        # ---------------- FINAL ORDER ----------------
        final_trainers = list(matched_trainers) + list(other_trainers)

        # ---------------- RESPONSE ----------------
        return Response({
            "status": True,
            "plan": {
                "id": plan.id,
                "name": plan.plan_name,
                "plan_type": plan.plan_type,
                
            },
            "client_address": client.address,
            "total_available": len(matched_trainers),
            "trainers": TrainerMiniSerializer(
                final_trainers,
                many=True,
                context={
                    "request": request,
                    "matched_ids": matched_ids
                }
            ).data
        }, status=status.HTTP_200_OK)



# for client to view trainer details in modal includig reviews
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from trainer.models import Trainer
from .serializers import TrainerDetailSerializer,TrainerClientSessionSerializer

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
from math import radians, sin, cos, asin, sqrt
from datetime import timedelta
from django.shortcuts import get_object_or_404

from trainer.models import Trainer, TrainerAvailability,SlotBooking, Payment
from client.models import Client
from plan.models import Plan
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ChangeTrainerSerializer


from math import radians, sin, cos, asin, sqrt
from datetime import timedelta
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from trainer.models import Trainer, TrainerAvailability
from client.models import Client
from trainer.serializers import ChangeTrainerSerializer
from decimal import Decimal
from .utils import get_plan_amount


class ChangeTrainerView(APIView):
    permission_classes = [IsAuthenticated]

    # ------------------ DISTANCE ------------------
    def haversine(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 6371 * (2 * asin(sqrt(a)))  # KM

    # ------------------ API ------------------
    def get(self, request):
        trainer_id = request.query_params.get("trainer_id")
        if not trainer_id:
            return Response(
                {"status": False, "message": "trainer_id is required"},
                status=400,
            )

        # ---------- CLIENT ----------
        client = get_object_or_404(Client, user=request.user)

        if not client.latitude or not client.longitude:
            return Response(
                {"status": False, "message": "Client location not set"},
                status=400,
            )

        # ---------- CURRENT BOOKING (FOR THIS TRAINER ONLY) ----------
        booking = (
            SlotBooking.objects
            .filter(client=client, trainer_id=trainer_id)
            .order_by("-date")
            .first()
        )

        if not booking:
            return Response(
                {"status": False, "message": "No booking found for this trainer"},
                status=400,
            )

        current_trainer = booking.trainer

        # ✅ UNIQUE PLAN COMES FROM TRAINER (NO CLIENT CONFLICT)
        plan = current_trainer.training_field

        booking_type = booking.booking_type
        time_slot = booking.time
        start_date = booking.date
        price_per_session = get_plan_amount(current_trainer, booking_type)
        total_sessions = current_trainer.no_of_section or 0

        paid_amount = price_per_session 

        # paid_amount = booking.amount_paid or 0
        total_sessions = current_trainer.no_of_section or 0

        # ---------- PLAN DURATION ----------
        duration_map = {"3_days": 3, "6_days": 6}
        duration = duration_map.get(plan.plan_type, 30)
        end_date = start_date + timedelta(days=duration)

        # ---------- WEEKDAYS ----------
        weekday_map = {
            0: "mon", 1: "tue", 2: "wed",
            3: "thu", 4: "fri", 5: "sat", 6: "sun"
        }

        existing_bookings = SlotBooking.objects.filter(
            client=client,
            trainer=current_trainer,
        )

        slot_days = list({weekday_map[b.date.weekday()] for b in existing_bookings})
        wanted_weekdays = [b.date.weekday() for b in existing_bookings]

        # ✅ SAFETY FALLBACK (CRITICAL)
        if not wanted_weekdays:
            wanted_weekdays = [start_date.weekday()]

        # ---------- BASE TRAINERS (SAME PLAN ONLY) ----------
        trainers = Trainer.objects.filter(
            training_field=plan,
            status="approved",
            gender__iexact=client.gender,
        ).exclude(id=current_trainer.id)

        matched = []
        others = []

        # ---------- FILTERING ----------
        for tr in trainers:

            # ----- PER SESSION PRICE -----
            if booking_type == "single":
                per_price = tr.single_price
            elif booking_type == "couple":
                per_price = tr.couple_price
            else:
                per_price = tr.group_price

            if not per_price:
                continue

            # ----- TOTAL & PRICE DIFFERENCE -----
            new_total = per_price * total_sessions
            price_difference = paid_amount - per_price
            # 🔴 DO NOT FILTER NEGATIVE (CLIENT MAY PAY EXTRA)

            # ----- DISTANCE -----
            if tr.latitude and tr.longitude:
                distance = self.haversine(
                    client.latitude,
                    client.longitude,
                    tr.latitude,
                    tr.longitude,
                )
                if distance > 5:
                    tr.price_difference = price_difference
                    others.append(tr)
                    continue

            # ----- AVAILABILITY -----
            try:
                avl = tr.traineravailability
            except TrainerAvailability.DoesNotExist:
                tr.price_difference = price_difference
                others.append(tr)
                continue

            if not all(getattr(avl, d) for d in slot_days):
                tr.price_difference = price_difference
                others.append(tr)
                continue

            if not (avl.start_time <= time_slot <= avl.end_time):
                tr.price_difference = price_difference
                others.append(tr)
                continue

            # ----- SESSION DATES -----
            session_dates = []
            d = start_date

            while len(session_dates) < total_sessions and d <= end_date:
                if d.weekday() in wanted_weekdays:
                    session_dates.append(d)
                d += timedelta(days=1)

            # ----- BOOKING CONFLICT -----
            conflict = SlotBooking.objects.filter(
                trainer=tr,
                date__in=session_dates,
                time=time_slot,
            ).exists()

            if conflict:
                tr.price_difference = price_difference
                others.append(tr)
                continue

            # ✅ MATCHED
            tr.price_difference = price_difference
            matched.append(tr)

        # ---------- FINAL ORDER ----------
        final_trainers = matched + others

        # ---------- RESPONSE ----------
        return Response({
            "status": True,
            "plan": {
                "id": plan.id,
                "name": plan.plan_name,
                "plan_type": plan.plan_type,
            },
            "client_address": client.address,
            "paid_amount": paid_amount,
            "total_available": len(matched),
            "trainers": ChangeTrainerSerializer(
                final_trainers,
                many=True,
                context={"request": request},
            ).data,
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


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class AddSlotBookingNoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = SlotBooking.objects.get(
                id=booking_id,
                trainer__user=request.user
            )
        except SlotBooking.DoesNotExist:
            return Response(
                {"error": "Booking not found or not authorized"},
                status=404
            )

        note_text = request.data.get("note")
        if not note_text:
            return Response(
                {"error": "Note is required"},
                status=400
            )

        booking.notes = note_text
        booking.save(update_fields=["notes"])

        return Response(
            {
                "message": "Note saved successfully",
                "booking_id": booking.id,
                "note": booking.notes
            },
            status=200
        )

class SlotBookingNoteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        try:
            booking = SlotBooking.objects.get(
                id=booking_id,
                trainer__user=request.user
            )
        except SlotBooking.DoesNotExist:
            return Response(
                {"error": "Booking not found or not authorized"},
                status=404
            )

        return Response(
            {
                "booking_id": booking.id,
                "note": booking.notes or ""
            },
            status=200
        )

class DeleteSlotBookingNoteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, booking_id):
        try:
            booking = SlotBooking.objects.get(
                id=booking_id,
                trainer__user=request.user
            )
        except SlotBooking.DoesNotExist:
            return Response(
                {"error": "Booking not found or not authorized"},
                status=404
            )

        booking.notes = ""
        booking.save(update_fields=["notes"])

        return Response(
            {
                "message": "Note deleted successfully",
                "booking_id": booking.id
            },
            status=200
        )

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class EditSlotBookingNoteView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, booking_id):
        booking = get_object_or_404(
            SlotBooking,
            id=booking_id,
            trainer__user=request.user
        )

        note_text = request.data.get("note")
        if not note_text:
            return Response(
                {"error": "Note is required"},
                status=400
            )

        booking.notes = note_text
        booking.save(update_fields=["notes"])

        return Response(
            {
                "message": "Note updated successfully",
                "booking_id": booking.id,
                "note": booking.notes
            },
            status=200
        )


from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class SuspendTrainerView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, trainer_id):
        trainer = get_object_or_404(
            Trainer,
            id=trainer_id,
            is_deleted=False
        )

        if not trainer.user:
            return Response(
                {"error": "Trainer user account not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Disable login
        trainer.user.is_active = False
        trainer.user.save(update_fields=["is_active"])

        # Soft delete / archive trainer
        trainer.is_deleted = True
        trainer.deleted_at = timezone.now()
        trainer.save(update_fields=["is_deleted", "deleted_at"])

        return Response(
            {
                "message": "Trainer suspended successfully",
                "trainer_id": trainer.id,
                "user_id": trainer.user.id,
                "is_active": trainer.user.is_active,
                "is_deleted": trainer.is_deleted,
            },
            status=status.HTTP_200_OK
        )


# trainer/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from .models import TrainerPayment
from .serializers import TrainerPaymentSerializer,OngoingSessionSerializer

class TrainerPaymentStatusUpdate(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, payment_id):
        payment = get_object_or_404(TrainerPayment, id=payment_id)

        payment.salary = request.data.get("salary", payment.salary)
        payment.status = request.data.get("status", payment.status)
        payment.remarks = request.data.get("remarks", payment.remarks)

        payment.save()

        return Response({
            "message": "Payment updated successfully",
            "data": TrainerPaymentSerializer(payment).data
        })


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import localdate

class OngoingSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trainer = request.user.trainer

        ongoing_session = SlotBooking.objects.filter(
            trainer=trainer,
            status="ongoing",
            date=localdate()
        ).select_related("trainer").first()

        if not ongoing_session:
            return Response(
                {"message": "No ongoing session"},
                status=200
            )

        serializer = OngoingSessionSerializer(ongoing_session)
        return Response(serializer.data, status=200)
    

from django.db.models import OuterRef, Subquery
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

class TrainerClientsListView(ListAPIView):
    serializer_class = TrainerClientSessionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        trainer = self.request.user.trainer

        # Subquery: next upcoming session per client
        next_session = (
            SlotBooking.objects
            .filter(
                trainer=trainer,
                client=OuterRef("client"),
                status="upcoming"
            )
            .order_by("date", "time")
            .values("id")[:1]
        )

        return (
            SlotBooking.objects
            .filter(
                trainer=trainer,
                status="upcoming",
                id=Subquery(next_session)
            )
            .select_related("client")
            .order_by("date", "time")
        )



from trainer.models import TrainerPayment
from trainer.serializers import TrainerPaymentSerializer

class TrainerPaymentListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        trainer_id = request.query_params.get("trainer_id")

        if not trainer_id:
            return Response(
                {"status": False, "message": "trainer_id is required"},
                status=400
            )

        payments = TrainerPayment.objects.filter(
            trainer_id=trainer_id
        ).order_by("-year", "-month")

        serializer = TrainerPaymentSerializer(payments, many=True)

        return Response({
            "status": True,
            "count": payments.count(),
            "data": serializer.data
        })
    


from rest_framework.generics import UpdateAPIView
from trainer.models import TrainerPayment
from trainer.serializers import TrainerPaymentUpdateSerializer

class TrainerPaymentUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = TrainerPayment.objects.all()
    serializer_class = TrainerPaymentUpdateSerializer


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from trainer.models import TrainerPayment
from trainer.utils import send_trainer_invoice_email

class TrainerPaymentInvoiceView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        try:
            payment = TrainerPayment.objects.select_related("trainer").get(id=pk)
        except TrainerPayment.DoesNotExist:
            return Response({"status": False, "message": "Payment not found"}, status=404)

        trainer = payment.trainer

        subject = f"Salary Invoice - {payment.get_month_display()} {payment.year}"

        message = f"""
Hello {trainer.name},

Here is your salary invoice:

-----------------------------------
Month      : {payment.get_month_display()} {payment.year}
Salary     : ₹{payment.salary}
Status     : {payment.status.upper()}
Paid Date  : {payment.paid_date or "Not Paid"}
-----------------------------------

If you have any questions, please contact HR.

Best regards,
HR Team
"""

        send_trainer_invoice_email(
            trainer.email,
            subject,
            message
        )

        return Response({
            "status": True,
            "message": "Invoice sent successfully"
        })





import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Payment
from .utils import get_plan_amount
from requests.exceptions import ConnectTimeout

class CreateTrainerBookingOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.debug("CreateTrainerBookingOrderView request data: %s", request.data)

        trainer_id = request.data.get("trainer_id")
        plan_id = request.data.get("plan_id")
        booking_type = request.data.get("booking_type")  # single/couple/group

        if not all([trainer_id, plan_id, booking_type]):
            return Response({"error": "Missing fields"}, 400)

        client = Client.objects.get(user=request.user)
        trainer = Trainer.objects.get(id=trainer_id, status="approved")
        plan = Plan.objects.get(id=plan_id)

        #  amount from trainer
        amount = get_plan_amount(trainer, booking_type)


        razorpay_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            order = razorpay_client.order.create(
                {
                    "amount": int(amount * 100),
                    "currency": "INR",
                    "payment_capture": 1
                },
                timeout=10  # ⬅️ ADD THIS
            )
        except ConnectTimeout:
            return Response(
                {"error": "Unable to connect to payment gateway. Try again later."},
                status=503
            )


        #  Save payment
        payment = Payment.objects.create(
            client=client,
            trainer=trainer,
            plan=plan,
            booking_type=booking_type,
            amount=amount,
            razorpay_order_id=order["id"],
            status="created"
        )

        return Response({
            "order_id": order["id"],
            "amount": amount,
            "currency": "INR",
            "key": settings.RAZORPAY_KEY_ID
        })


from razorpay.errors import SignatureVerificationError

from django.db import transaction
from razorpay.errors import SignatureVerificationError

from datetime import datetime, timedelta

class VerifyTrainerPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        start_date = request.data.get("start_date")
        time_slot = request.data.get("time")
        slot_days = request.data.get("slot_days")

        # ✅ VALIDATION (IMPORTANT)
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({"error": "Missing Razorpay details"}, 400)

        if not all([start_date, time_slot, slot_days]):
            return Response({
                "error": "start_date, time and slot_days are required"
            }, 400)

        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)

        # Prevent duplicate verification
        if payment.status == "success":
            return Response({
                "message": "Payment already verified",
                "total_sessions": SlotBooking.objects.filter(payment=payment).count()
            })

        razorpay_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })
        except SignatureVerificationError:
            payment.status = "failed"
            payment.save()
            return Response({"error": "Payment verification failed"}, 400)

        # ✅ SAFE PARSING
        try:
            time_slot_obj = datetime.strptime(time_slot, "%H:%M").time()
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date or time format"}, 400)

        slot_days = [d.lower() for d in slot_days]

        weekday_map = {
            "mon": 0, "tue": 1, "wed": 2,
            "thu": 3, "fri": 4, "sat": 5, "sun": 6
        }

        try:
            selected_weekdays = [weekday_map[d] for d in slot_days]
        except KeyError:
            return Response({"error": "Invalid slot_days"}, 400)

        trainer = payment.trainer
        client = payment.client
        plan = payment.plan

        max_sessions = trainer.no_of_section
        session_dates = []

        d = start_date_obj
        filled = 0

        while filled < max_sessions:
            if d.weekday() in selected_weekdays:
                session_dates.append(d)
                filled += 1
            d += timedelta(days=1)

        # 🔒 Conflict check
        if SlotBooking.objects.filter(
            trainer=trainer,
            date__in=session_dates,
            time=time_slot_obj
        ).exists():
            return Response({"error": "Trainer already booked"}, 400)

        # ✅ ATOMIC SAVE
        with transaction.atomic():
            payment.status = "success"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.save()

            for date in session_dates:
                SlotBooking.objects.create(
                    trainer=trainer,
                    client=client,
                    plan=plan,
                    booking_type=payment.booking_type,
                    amount_paid=payment.amount,
                    payment=payment,
                    date=date,
                    time=time_slot_obj,
                    payment_status="paid"
                )

        return Response({
            "message": "Payment verified & slots booked successfully",
            "total_sessions": len(session_dates)
        })
from django.db import transaction
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import razorpay
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import razorpay

class CreateTrainerChangeOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = Client.objects.get(user=request.user)

        new_trainer_id = request.data.get("new_trainer_id")
        plan_id = request.data.get("plan_id")

        if not new_trainer_id or not plan_id:
            return Response({"error": "Missing fields"}, 400)

        new_trainer = Trainer.objects.get(id=new_trainer_id, status="approved")
        plan = Plan.objects.get(id=plan_id)

        old_slots = SlotBooking.objects.filter(
            client=client,
            plan=plan,
            status="upcoming"
        )

        if not old_slots.exists():
            return Response({"error": "No remaining sessions"}, 400)

        first_slot = old_slots.first()
        booking_type = first_slot.booking_type
        remaining_sessions = old_slots.count()

        old_price_per_session = float(first_slot.amount_paid)
        new_price_per_session = float(
            get_plan_amount(new_trainer, booking_type)
        )

        diff = new_price_per_session - old_price_per_session

        # 🔹 CASE 1: NO PAYMENT REQUIRED
        if diff <= 0:
            return Response({
                "order_required": False,
                "verify_required": True,
                "remaining_sessions": remaining_sessions
            })

        # 🔹 CASE 2: PAYMENT REQUIRED
        total_amount = diff 

        razorpay_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        order = razorpay_client.order.create({
            "amount": int(total_amount * 100),
            "currency": "INR",
            "payment_capture": 1
        })

        Payment.objects.create(
            client=client,
            trainer=new_trainer,
            plan=plan,
            booking_type=booking_type,
            amount=total_amount,
            razorpay_order_id=order["id"],
            status="created"
        )

        return Response({
            "order_required": True,
            "order_id": order["id"],
            "amount": total_amount,
            "key": settings.RAZORPAY_KEY_ID
        })


from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from razorpay.errors import SignatureVerificationError
import razorpay

class VerifyTrainerChangePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = Client.objects.get(user=request.user)

        razorpay_order_id = request.data.get("razorpay_order_id")
        old_trainer_id = request.data.get("old_trainer_id")
        new_trainer_id = request.data.get("new_trainer_id")
        plan_id = request.data.get("plan_id")

        # ---------------------------------------------------
        # 🔹 CASE 1: NO PAYMENT REQUIRED
        # ---------------------------------------------------
        if not razorpay_order_id:
            plan = Plan.objects.get(id=plan_id)
            new_trainer = Trainer.objects.get(id=new_trainer_id)

            old_slots_qs = SlotBooking.objects.filter(
                client=client,
                plan=plan,
                status="upcoming"
            )

            if not old_slots_qs.exists():
                return Response({"error": "No upcoming sessions"}, status=400)

            old_slots = list(old_slots_qs)  # ✅ FREEZE DATA

            with transaction.atomic():
                old_slots_qs.update(status="changed")

                for slot in old_slots:
                    SlotBooking.objects.create(
                        trainer=new_trainer,
                        client=client,
                        plan=plan,
                        booking_type=slot.booking_type,
                        amount_paid=slot.amount_paid,
                        date=slot.date,
                        time=slot.time,
                        status="upcoming",
                        payment_status="paid"
                    )

            return Response({"status": True, "no_payment": True})


        # ---------------------------------------------------
        # 🔹 CASE 2: PAYMENT FLOW
        # ---------------------------------------------------
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        payment = Payment.objects.filter(
            razorpay_order_id=razorpay_order_id,
            client=client,
            status="created"
        ).first()

        if not payment:
            return Response({"error": "Invalid order"}, status=400)

        razorpay_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })
        except SignatureVerificationError:
            return Response({"error": "Signature verification failed"}, status=400)

        # 🔹 Fetch old slots BEFORE update
        old_slots_qs = SlotBooking.objects.filter(
            client=client,
            plan=payment.plan,
            status="upcoming"
        )

        count = old_slots_qs.count()
        if count == 0:
            return Response({"error": "No upcoming sessions"}, status=400)

        old_slots = list(old_slots_qs)  
        per_session_amount = payment.amount

        with transaction.atomic():
            payment.status = "success"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.save(update_fields=[
                "status",
                "razorpay_payment_id",
                "razorpay_signature"
            ])

            # ✅ MARK OLD SLOTS
            old_slots_qs.update(status="changed")

            # ✅ CREATE NEW SLOTS (FIX #2)
            for slot in old_slots:
                SlotBooking.objects.create(
                    trainer=payment.trainer,  # NEW trainer already saved in payment
                    client=client,
                    plan=payment.plan,
                    booking_type=payment.booking_type,
                    amount_paid=per_session_amount,
                    date=slot.date,
                    time=slot.time,
                    status="upcoming",
                    payment_status="paid"
                )

        return Response({"status": True})



from django.db.models import Count
from django.db.models.functions import ExtractMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Trainer
from client.models import Client


class MonthlyTrainerClientCountAPIView(APIView):
    """
    Returns month-wise Trainer and Client count for a given year.

    Example:
    GET /api/dashboard/monthly-count/?year=2026
    """

    def get(self, request):
        year = request.query_params.get("year")

        if not year:
            return Response(
                {"error": "Year parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            year = int(year)
        except ValueError:
            return Response(
                {"error": "Invalid year."},
                status=status.HTTP_400_BAD_REQUEST
            )

        trainer_data = (
            Trainer.objects.filter(created_at__year=year)
            .annotate(month=ExtractMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
        )

        client_data = (
            Client.objects.filter(created_at__year=year)
            .annotate(month=ExtractMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
        )

        trainer_dict = {item["month"]: item["count"] for item in trainer_data}
        client_dict = {item["month"]: item["count"] for item in client_data}

        months = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]

        response = []

        for month in range(1, 13):
            response.append({
                "month": months[month - 1],
                "trainer_count": trainer_dict.get(month, 0),
                "client_count": client_dict.get(month, 0),
            })

        return Response({
            "year": year,
            "data": response
        })
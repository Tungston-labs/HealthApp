from django.shortcuts import render
from client.models import Client
from .serializers import TodaySessionSerializer,ClientDetailSerializer,HistoryBookingSerializer,AllBookingSerializer
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import datetime
from datetime import datetime, date
from trainer.models import Trainer, SlotBooking
from .serializers import AllBookingSerializer
from rest_framework.views import APIView
from datetime import datetime, time
from trainer.models import Trainer, SlotBooking
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from trainer.models import SlotBooking
from trainer.serializers import TrainerMiniSerializer
from rest_framework import generics, permissions
from trainer.models import SlotBooking
from .serializers import ClientSessionHistorySerializer,AdminTrainerSessionSerializer

from django.db.models import Min, Max
from rest_framework import generics
from rest_framework.response import Response
from accounts.permissions import IsAdmin
from accounts.paginations import CustomPagination

class ClientPlanSummaryAPIView(generics.GenericAPIView):
    def get(self, request, client_id):
        bookings = SlotBooking.objects.filter(client_id=client_id)

        if not bookings.exists():
            return Response([])

        grouped = {}

        for book in bookings:
            key = f"{book.trainer_id}-{book.plan_id}"

            if key not in grouped:
                grouped[key] = {
                    "trainer_name": book.trainer.name,
                    "plan_type": book.plan.plan_type,
                    "start_date": book.date,
                    "end_date": book.date,
                    "amount": float(book.plan.single_price),
                }
            else:
                # update earliest start and latest end
                if book.date < grouped[key]["start_date"]:
                    grouped[key]["start_date"] = book.date
                if book.date > grouped[key]["end_date"]:
                    grouped[key]["end_date"] = book.date

        # Convert to list and calculate session period
        output = []
        for item in grouped.values():
            start = item["start_date"]
            end = item["end_date"]

            weeks = ((end - start).days + 1) // 7
            if weeks == 0:
                weeks = 1

            item["session_period"] = f"{weeks} Weeks"

            output.append(item)

        return Response(output)

from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from datetime import date

class TrainerTodaySessionsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TodaySessionSerializer

    def get(self, request):
        trainer = Trainer.objects.get(user=request.user)
        today = date.today()

        queryset = SlotBooking.objects.filter(
            trainer=trainer,
            date=today
        ).order_by("time")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

class ClientDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        serializer = ClientDetailSerializer(client, context={"request": request})
        return Response(serializer.data)



from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import date, datetime
from django.db.models import Q

from datetime import date, datetime
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class TrainerAllBookingsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = AllBookingSerializer

    def get(self, request):
        trainer = Trainer.objects.get(user=request.user)
        filter_date = request.query_params.get("date")

        # 🔹 If specific date is provided
        if filter_date:
            try:
                filter_date = datetime.strptime(filter_date, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=400
                )

            queryset = SlotBooking.objects.filter(
                trainer=trainer,
                date=filter_date,
                status="upcoming"  # ✅ KEY FIX
            ).order_by("time")

        else:
            today = date.today()

            # 🔹 TODAY → upcoming only, nearest time first
            today_sessions = SlotBooking.objects.filter(
                trainer=trainer,
                date=today,
                status="upcoming"
            ).order_by("time")

            # 🔹 FUTURE → upcoming only
            upcoming_sessions = SlotBooking.objects.filter(
                trainer=trainer,
                date__gt=today,
                status="upcoming"
            ).order_by("date", "time")

            queryset = today_sessions | upcoming_sessions

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)


    
class TrainerHistorySessionsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = AllBookingSerializer

    def get(self, request):
        trainer = Trainer.objects.get(user=request.user)

        queryset = SlotBooking.objects.filter(
            trainer=trainer,
            status="completed"
        ).order_by("-session_end_date", "-session_end_time")

        filter_date = request.query_params.get("date")
        if filter_date:
            try:
                filter_date = datetime.strptime(filter_date, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format"}, status=400)

            queryset = queryset.filter(session_end_date=filter_date)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)




from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import now

class StartTrainingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            trainer = Trainer.objects.get(user=request.user)
        except Trainer.DoesNotExist:
            return Response({"error": "Trainer not found"}, status=404)

        booking_id = request.data.get("booking_id")
        if not booking_id:
            return Response({"error": "Booking ID is required"}, status=400)

        try:
            booking = SlotBooking.objects.get(id=booking_id, trainer=trainer)
        except SlotBooking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        if booking.status != "upcoming":
            return Response(
                {"error": f"Cannot start session with status {booking.status}"},
                status=400
            )

        # ✅ UPDATE STATUS + API HIT TIME
        booking.status = "ongoing"
        booking.session_start_apihit_time = now()
        booking.save(update_fields=["status", "session_start_apihit_time"])

        return Response({
            "message": "Training started",
            "booking_id": booking.id,
            "status": booking.status,
            "session_start_apihit_time": booking.session_start_apihit_time
        }, status=200)

    
from django.utils import timezone
from zoneinfo import ZoneInfo    
class EndTrainingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        trainer = Trainer.objects.get(user=request.user)
        booking_id = request.data.get("booking_id")

        if not booking_id:
            return Response({"error": "Booking ID is required"}, status=400)

        try:
            booking = SlotBooking.objects.get(id=booking_id, trainer=trainer)
        except SlotBooking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        if booking.status != "ongoing":
            return Response({"error": f"Cannot end session with status {booking.status}"}, status=400)

        # Convert current time to IST
        ist_now = timezone.now().astimezone(ZoneInfo("Asia/Kolkata"))

        booking.status = "completed"
        booking.session_end_date = ist_now.date()
        booking.session_end_time = ist_now.time()
        booking.save()

        return Response({
            "message": "Training session ended",
            "booking_id": booking.id,
            "status": booking.status,
            "session_end_date": booking.session_end_date,
            "session_end_time": booking.session_end_time
        })


# for getting all sessions for client



from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

class ClientCompletedSessionsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request):
        client = request.user.client  # OneToOne assumed

        queryset = SlotBooking.objects.filter(
            client=client,
            status='completed'
        ).order_by('-date', '-time')

        page = self.paginate_queryset(queryset)

        sessions_data = [
            {
                "section_id": s.id,
                "date": s.date,
                "time": s.time,
                "trainer": TrainerMiniSerializer(
                    s.trainer, context={"request": request}
                ).data,
                "notes": getattr(s, "notes", None)
            }
            for s in page
        ]

        return self.get_paginated_response({
            "sessions": sessions_data
        })

# for getting details about single sessions

class ClientSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = SlotBooking.objects.get(id=session_id, client=request.user.client)
        except SlotBooking.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)

        data = {
            "section_id": session.id,
            "date": session.date,
            "time": session.time,
            "status": session.status,
            "session_end_date": session.session_end_date,
            "session_end_time": session.session_end_time,
            "notes": session.notes if hasattr(session, "notes") else None,
            "trainer": TrainerMiniSerializer(session.trainer, context={"request": request}).data
        }

        return Response(data)
    
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import localdate

class ClientTodaySessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = request.user.client
        today = localdate()

        try:
            session = SlotBooking.objects.get(
                client=client,
                date=today
            )
        except SlotBooking.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "No session scheduled for today"
                },
                status=404
            )

        data = {
            "section_id": session.id,
            "date": session.date,
            "time": session.time,
            "time_label": session.time_label,
            "status": session.status,
            "session_end_date": session.session_end_date,
            "session_end_time": session.session_end_time,
            "notes": session.notes if hasattr(session, "notes") else None,
            "section_timing": {
                "value": session.section_timing,
                "label": session.get_section_timing_display()
            },
            "trainer": TrainerMiniSerializer(
                session.trainer,
                context={"request": request}
            ).data
        }

        return Response({
            "status": True,
            "data": data
        })

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from django.utils import timezone
from zoneinfo import ZoneInfo

from trainer.models import SlotBooking


from datetime import datetime
from zoneinfo import ZoneInfo
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from trainer.models import SlotBooking

class ClientWeeklyHoursAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):

        # Get completed sessions ordered by date
        sessions = SlotBooking.objects.filter(
            client_id=client_id,
            status="completed"
        ).order_by("date")

        if not sessions.exists():
            return Response({
                "client_id": client_id,
                "weeks": {}
            })

        # First session date = start of week1
        first_session_date = sessions.first().date

        weekly_hours = {}

        for session in sessions:

            if not session.date or not session.time or not session.session_end_date or not session.session_end_time:
                continue

            # Convert datetimes to IST
            start_dt = datetime.combine(session.date, session.time).replace(
                tzinfo=ZoneInfo("Asia/Kolkata")
            )
            end_dt = datetime.combine(session.session_end_date, session.session_end_time).replace(
                tzinfo=ZoneInfo("Asia/Kolkata")
            )

            # Duration in hours
            duration_hours = (end_dt - start_dt).total_seconds() / 3600

            # Calculate week index from first session
            days_diff = (session.date - first_session_date).days
            week_number = (days_diff // 7) + 1

            week_label = f"Week {week_number}"

            # Add to weekly total
            weekly_hours[week_label] = weekly_hours.get(week_label, 0) + round(duration_hours, 2)

        return Response({
            "client_id": client_id,
            "weeks": weekly_hours
        })

from django.shortcuts import get_object_or_404
from django.db.models import Min, Max
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import date
from math import ceil


# view trainers session by admin
from django.db.models import Min, Max
from math import ceil
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class AdminTrainerSessionsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, trainer_id):
        trainer = get_object_or_404(Trainer, id=trainer_id)

        bookings = (
            SlotBooking.objects
            .filter(trainer=trainer)
            .values(
                "client",
                "client__name",
                "client__profile_pic",
            )
            .annotate(
                start_date=Min("date"),
                end_date=Max("date"),
            )
            .order_by("-end_date")
        )

        sessions = []
        for item in bookings:
            start = item["start_date"]
            end = item["end_date"]

            total_days = (end - start).days + 1
            weeks = ceil(total_days / 7)

            sessions.append({
                "trainer_name": trainer.name,
                "trainer_profile": (
                    request.build_absolute_uri(trainer.profile_pic.url)
                    if trainer.profile_pic else None
                ),

                # ✅ CLIENT DETAILS
                "client_id": item["client"],
                "client_name": item["client__name"],
                "client_profile": (
                    request.build_absolute_uri(item["client__profile_pic"])
                    if item["client__profile_pic"] else None
                ),

                "start_date": start,
                "end_date": end,
                "session_period": f"{weeks} weeks",
            })

        return Response({
            "trainer_id": trainer.id,
            "trainer_name": trainer.name,
            "total_clients": len(sessions),
            "sessions": sessions
        })



from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import SlotBookingDetailSerializer

class TrainerSlotBookingDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SlotBookingDetailSerializer

    def get_queryset(self):
        trainer = Trainer.objects.get(user=self.request.user)
        return SlotBooking.objects.select_related(
            "client", "plan", "trainer"
        ).filter(trainer=trainer)

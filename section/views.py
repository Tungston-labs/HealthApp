from django.shortcuts import render
from client.models import Client
from .serializers import TodaySessionSerializer,ClientDetailSerializer,HistoryBookingSerializer,AllBookingSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
from .serializers import ClientSessionHistorySerializer

from django.db.models import Min, Max
from rest_framework import generics
from rest_framework.response import Response

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

class TrainerTodaySessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trainer = Trainer.objects.get(user=request.user)
        today = date.today()

        sessions = SlotBooking.objects.filter(
            trainer=trainer,
            date=today
        ).order_by("time")

        serializer = TodaySessionSerializer(
            sessions, many=True, context={"request": request}
        )
        return Response({"total_sessions": len(sessions), "sessions": serializer.data})
class ClientDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        serializer = ClientDetailSerializer(client, context={"request": request})
        return Response(serializer.data)



class TrainerAllBookingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trainer = Trainer.objects.get(user=request.user)

        filter_date = request.query_params.get("date")
        if filter_date:
            try:
                filter_date = datetime.strptime(filter_date, "%Y-%m-%d").date()
            except:
                return Response({"error": "Invalid date format"}, status=400)

            bookings = SlotBooking.objects.filter(
                trainer=trainer,
                date=filter_date
            ).order_by("time")
        else:
            bookings = SlotBooking.objects.filter(
                trainer=trainer,
                date__gte=date.today()
            ).order_by("date", "time")

        serializer = AllBookingSerializer(bookings, many=True, context={"request": request})
        return Response({
            "total": len(bookings),
            "bookings": serializer.data
        })

class TrainerHistorySessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trainer = Trainer.objects.get(user=request.user)

        filter_date = request.query_params.get("date")

        history_qs = SlotBooking.objects.filter(
            trainer=trainer,
            status="completed"
        ).order_by("-session_end_date", "-session_end_time")

        if filter_date:
            try:
                filter_date = datetime.strptime(filter_date, "%Y-%m-%d").date()
            except:
                return Response({"error": "Invalid date format"}, 400)

            history_qs = history_qs.filter(session_end_date=filter_date)

        serializer = AllBookingSerializer(history_qs, many=True, context={"request": request})
        return Response({
            "total_completed": len(history_qs),
            "sessions": serializer.data
        })




class StartTrainingView(APIView):
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

        if booking.status != "upcoming":
            return Response({"error": f"Cannot start session with status {booking.status}"}, status=400)

        booking.status = "ongoing"
        booking.save()

        return Response({
            "message": "Training started",
            "booking_id": booking.id,
            "status": booking.status
        })
    
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



class ClientCompletedSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = request.user.client  # assuming OneToOne
        sessions = SlotBooking.objects.filter(
            client=client,
            status='completed'
        ).order_by('-date', '-time')

        response_data = [
            {
                "section_id": s.id,
                "date": s.date,
                "time": s.time,
                "trainer": TrainerMiniSerializer(s.trainer, context={"request": request}).data,
                "notes": s.notes if hasattr(s, "notes") else None
            }
            for s in sessions
        ]

        return Response({
            "total_completed_sessions": len(sessions),
            "sessions": response_data
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


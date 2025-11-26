from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import TrainingCancelRequest
from trainer.models import SlotBooking

class RequestTrainingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = request.user.client

        # 1. Fetch latest active (upcoming/ongoing) session
        slot = SlotBooking.objects.filter(
            client=client,
            status__in=["upcoming", "ongoing"]
        ).order_by("date", "time").first()

        if not slot:
            return Response({"error": "No active session available to cancel"}, status=404)

        # 2. Prevent duplicate cancellation request
        if TrainingCancelRequest.objects.filter(slot=slot, status="open").exists():
            return Response({"error": "Cancellation already requested"}, status=400)

        # 3. Create cancellation request
        cancel_req = TrainingCancelRequest.objects.create(
            client=client,
            trainer=slot.trainer,
            plan=slot.plan,
            slot=slot,
            amount=slot.plan.single_price  # choose appropriate price logic
        )

        return Response({
            "message": "Cancellation request submitted",
            "request_id": cancel_req.id
        }, status=201)
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .models import TrainingCancelRequest
from .serializers import TrainingCancelRequestSerializer

class ClientCancelRequestListView(ListAPIView):
    serializer_class = TrainingCancelRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        client = self.request.user.client
        return TrainingCancelRequest.objects.filter(client=client).order_by("-request_date")
# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser

from .models import TrainingCancelRequest
from .serializers import (
    TrainingCancelListSerializer,
    TrainingCancelDetailSerializer,
    TrainingCancelStatusUpdateSerializer
)

class TrainingCancelListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        requests = TrainingCancelRequest.objects.select_related(
            "client", "trainer", "plan", "slot"
        ).order_by("-request_date")

        serializer = TrainingCancelListSerializer(requests, many=True)
        return Response(serializer.data, status=200)
class TrainingCancelDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            cancel_request = TrainingCancelRequest.objects.select_related(
                "client", "trainer", "plan", "slot"
            ).get(id=pk)
        except TrainingCancelRequest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        serializer = TrainingCancelDetailSerializer(cancel_request)
        return Response(serializer.data, status=200)
class TrainingCancelStatusUpdateView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            cancel_request = TrainingCancelRequest.objects.get(id=pk)
        except TrainingCancelRequest.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        serializer = TrainingCancelStatusUpdateSerializer(
            cancel_request, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Status updated successfully"}, status=200)

        return Response(serializer.errors, status=400)

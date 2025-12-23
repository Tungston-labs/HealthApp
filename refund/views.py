from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import TrainingCancelRequest
from trainer.models import SlotBooking
from rest_framework.generics import ListAPIView
from .serializers import TrainingCancelRequestSerializer
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .models import TrainingCancelRequest
from .serializers import (
    TrainingCancelListSerializer,
    TrainingCancelDetailSerializer,
    TrainingCancelStatusUpdateSerializer
)
from accounts.paginations import CustomPagination

class RequestTrainingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = request.user.client

        # 1. Get latest active slot
        slot = (
            SlotBooking.objects.filter(
                client=client,
                status__in=["upcoming", "ongoing"]
            )
            .order_by("date", "time")
            .first()
        )

        if not slot:
            return Response(
                {"error": "No active session available to cancel"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Prevent duplicate requests
        if TrainingCancelRequest.objects.filter(slot=slot, status="open").exists():
            return Response(
                {"error": "Cancellation already requested"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Create request
        cancel_req = TrainingCancelRequest.objects.create(
            client=client,
            trainer=slot.trainer,
            plan=slot.plan,
            slot=slot,
            amount=slot.plan.single_price
        )

        return Response(
            {
                "message": "Cancellation request submitted",
                "request_id": cancel_req.id
            },
            status=status.HTTP_201_CREATED
        )


class ClientCancelRequestListView(ListAPIView):
    serializer_class = TrainingCancelRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        client = self.request.user.client
        return TrainingCancelRequest.objects.filter(client=client).order_by("-request_date")


from rest_framework import generics

class TrainingCancelListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = TrainingCancelListSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return TrainingCancelRequest.objects.select_related(
            "client", "trainer", "plan", "slot"
        ).order_by("-request_date")

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

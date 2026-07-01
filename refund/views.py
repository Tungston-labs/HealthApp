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
        slot_id = request.data.get("slot_id")
        trainer_id = request.data.get("trainer_id")

        slot_qs = SlotBooking.objects.filter(
            client=client,
            status__in=["upcoming", "ongoing"]
        )

        if trainer_id:
            slot_qs = slot_qs.filter(trainer_id=trainer_id)

        if slot_id:
            slot_qs = slot_qs.filter(id=slot_id)

        slot = slot_qs.order_by("date", "time").first()

        if not slot:
            return Response(
                {
                    "success": False,
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": "No active session available to cancel",
                    "errors": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if TrainingCancelRequest.objects.filter(slot=slot, status="open").exists():
            return Response(
                {
                    "success": False,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Cancellation already requested",
                    "errors": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cancel_req = TrainingCancelRequest.objects.create(
            client=client,
            trainer=slot.trainer,
            plan=slot.plan,
            slot=slot,
            amount=slot.amount_paid
        )

        return Response(
            {
                "success": True,
                "status_code": status.HTTP_201_CREATED,
                "message": "Cancellation request submitted",
                "data": {
                    "request_id": cancel_req.id
                }
            },
            status=status.HTTP_201_CREATED
        )


class ClientCancelRequestListView(ListAPIView):
    serializer_class = TrainingCancelRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response({
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Cancellation requests fetched",
            "data": serializer.data
        })

    def get_queryset(self):
        client = self.request.user.client
        return TrainingCancelRequest.objects.filter(client=client).order_by("-request_date")



from rest_framework import generics

class TrainingCancelListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = TrainingCancelListSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return (
            TrainingCancelRequest.objects
            .select_related("client", "trainer", "plan", "slot")
            .order_by("-request_date")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        limit = request.query_params.get("limit")
        if limit:
            queryset = queryset[:int(limit)]
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "success": True,
                "status_code": status.HTTP_200_OK,
                "message": "Latest cancellation requests",
                "count": len(serializer.data),
                "data": serializer.data
            })

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response({
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Cancellation requests list",
            "data": serializer.data
        })
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
            return Response(
                {"error": "Not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = cancel_request.status

        serializer = TrainingCancelStatusUpdateSerializer(
            cancel_request,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        new_status = serializer.instance.status

        
        if old_status != "closed" and new_status == "closed":

            SlotBooking.objects.filter(
                client=cancel_request.client,
                trainer=cancel_request.trainer,
                plan=cancel_request.plan,
                status__in=["upcoming", "ongoing"]
            ).update(status="cancelled")

        return Response(
            {
                "success": True,
                "message": "Status updated successfully"
            },
            status=status.HTTP_200_OK
        )
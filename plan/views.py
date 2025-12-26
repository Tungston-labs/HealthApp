# plans/views.py
from .models import Plan
from .serializers import PlanSerializer,PlanMiniSerializer
from accounts.permissions import IsAdmin,IsUser
from django.shortcuts import get_object_or_404
from accounts.paginations import CustomPagination
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Plan
from trainer.models import Trainer
from client.models import Client
from .serializers import PlanSerializer

class PlanListCreateView(generics.ListCreateAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAdmin]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Plan.objects.annotate(
            approved_trainers_count=Count(
                "trainers",
                filter=Q(trainers__status="approved")
            )
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "status": True,
            "data": response.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({
            "status": True,
            "message": "Plan created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class PlanRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAdmin]

    def get_object(self):
        return get_object_or_404(Plan, id=self.kwargs["pk"])

    def retrieve(self, request, *args, **kwargs):
        plan = self.get_object()
        serializer = self.get_serializer(plan)

        return Response({
            "status": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        plan = self.get_object()
        serializer = self.get_serializer(plan, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({
            "status": True,
            "message": "Plan updated successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        plan = self.get_object()

        trainer_exists = Trainer.objects.filter(training_field=plan).exists()

        if trainer_exists:
            return Response({
                "status": False,
                "message": "This plan cannot be deleted because trainers are assigned to it."
            }, status=status.HTTP_400_BAD_REQUEST)

        plan.delete()
        return Response({
            "status": True,
            "message": "Plan deleted successfully"
        }, status=status.HTTP_200_OK)

class PlanMiniListView(generics.ListAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanMiniSerializer
    permission_classes = [IsAdmin]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "status": True,
            "data": response.data
        }, status=status.HTTP_200_OK)


class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsUser]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "status": True,
            "data": response.data
        }, status=status.HTTP_200_OK)


class PlanDetailView(generics.RetrieveAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsUser]

    def get_object(self):
        return get_object_or_404(Plan, id=self.kwargs["pk"])

    def retrieve(self, request, *args, **kwargs):
        plan = self.get_object()
        serializer = self.get_serializer(plan)

        return Response({
            "status": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


from rest_framework import generics
from django.db.models import Count, Q
from plan.models import Plan
from .serializers import PlanPendingCountSimpleSerializer

class PlanPendingCountListView(generics.ListAPIView):
    serializer_class = PlanPendingCountSimpleSerializer

    def get_queryset(self):
        return Plan.objects.annotate(
            pending_count=Count(
                "trainers",
                filter=Q(trainers__status="pending")
            )
        )

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)

        return Response({
            "status": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

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
    queryset = Plan.objects.annotate(
        approved_trainers_count=Count(
            "trainers",
            filter=Q(trainers__status="approved")
        )
    ).order_by("-created_at")

    serializer_class = PlanSerializer
    permission_classes = [IsAdmin]
    pagination_class = CustomPagination

    



class PlanRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAdmin]

    def get_object(self):
        return get_object_or_404(Plan, id=self.kwargs["pk"])

    def destroy(self, request, *args, **kwargs):
        plan = self.get_object()

        # ✅ Check trainers linked to this plan
        trainer_exists = Trainer.objects.filter(training_field=plan).exists()

       

        if trainer_exists :
            return Response(
                {
                    "success": False,
                    "message": "This plan cannot be deleted because trainers or users are assigned to it."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        plan.delete()
        return Response(
            {
                "success": True,
                "message": "Plan deleted successfully."
            },
            status=status.HTTP_200_OK
        )

    
class PlanMiniListView(generics.ListAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanMiniSerializer
    permission_classes = [IsAdmin]

class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsUser]

class PlanDetailView(generics.RetrieveAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsUser]

    def get_object(self):
        return get_object_or_404(Plan, id=self.kwargs["pk"])



# getting plan list with pending trainer counts
# views.py
from rest_framework import generics
from django.db.models import Count, Q
from plan.models import Plan
from .serializers import PlanPendingCountSimpleSerializer

class PlanPendingCountListView(generics.ListAPIView):
    serializer_class = PlanPendingCountSimpleSerializer

    def get_queryset(self):
        return Plan.objects.annotate(
            pending_count=Count(
                'trainers',
                filter=Q(trainers__status='pending')
            )
        ).values('id', 'plan_name', 'pending_count')

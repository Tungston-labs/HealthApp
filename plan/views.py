# plans/views.py
from rest_framework import generics
from .models import Plan
from .serializers import PlanSerializer
from accounts.permissions import IsAdmin,IsUser
from django.shortcuts import get_object_or_404

class PlanListCreateView(generics.ListCreateAPIView):
    queryset = Plan.objects.all().order_by('-created_at')
    serializer_class = PlanSerializer
    permission_classes = [IsAdmin]
    
class PlanRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAdmin]

    def get_object(self):
        return get_object_or_404(Plan, id=self.kwargs["pk"])


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

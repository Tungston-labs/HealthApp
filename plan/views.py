# plans/views.py
from rest_framework import generics
from .models import Plan
from .serializers import PlanSerializer
from accounts.permissions import IsAdmin

class PlanListCreateView(generics.ListCreateAPIView):
    queryset = Plan.objects.all().order_by('-created_at')
    serializer_class = PlanSerializer
    permission_classes = [IsAdmin]
    
class PlanRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsAdmin]

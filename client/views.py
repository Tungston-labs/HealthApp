from rest_framework import generics, permissions,status
from django.shortcuts import get_object_or_404
from .models import Client
from .serializers import ClientSerializer,ClientProfileSerializer
from plan.models import Plan
from plan.serializers import PlanSerializer
from accounts.permissions import IsUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from trainer.models import Trainer
from client.models import Client
from nutrition.models import NutritionRequest
from tickets.models import Ticket
from refund.models import TrainingCancelRequest
from accounts.paginations import CustomPagination

class ClientCreateView(generics.CreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.AllowAny]  # anyone can register


# List clients (authenticated only)
from django.db.models import Q

class ClientListView(generics.ListAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Client.objects.all()

        search = self.request.query_params.get("search")  # 🔍 name search
        plan = self.request.query_params.get("plan")      # plan name
        plan_id = self.request.query_params.get("plan_id")  # plan id

        # 🔍 SEARCH BY NAME
        if search:
            queryset = queryset.filter(name__icontains=search)

        # 🔥 FILTER BY PLAN NAME
        if plan:
            queryset = queryset.filter(
                slotbooking__plan__plan_name__icontains=plan
            ).distinct()

        # 🔥 FILTER BY PLAN ID
        if plan_id:
            queryset = queryset.filter(
                slotbooking__plan__id=plan_id
            ).distinct()

        return queryset



# Retrieve, Update, Delete client profile (authenticated only)
from django.shortcuts import get_object_or_404

class ClientRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"



class DashboardCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = {
                "approved_trainers": Trainer.objects.filter(status="approved").count(),
                "client_count": Client.objects.count(),
                "pending_nutrition_requests": NutritionRequest.objects.filter(status="pending").count(),
                "plan_count": Plan.objects.count(),
                "open_tickets": Ticket.objects.filter(status="open").count(),
                "open_refund_requests": TrainingCancelRequest.objects.filter(status="open").count(),
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Something went wrong", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





class ClientProfileView(generics.RetrieveAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsUser]

    def get_object(self):
        return get_object_or_404(Client, user=self.request.user)


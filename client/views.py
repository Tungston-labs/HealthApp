from rest_framework import generics, permissions
from .models import Client
from .serializers import ClientSerializer,ClientProfileSerializer
from plan.models import Plan
from plan.serializers import PlanSerializer
from accounts.permissions import IsUser

class ClientCreateView(generics.CreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.AllowAny]  # anyone can register


# List clients (authenticated only)
class ClientListView(generics.ListAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

# Retrieve, Update, Delete client profile (authenticated only)
class ClientRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Optional: restrict access to only the logged-in user
    def get_object(self):
        return Client.objects.get(user=self.request.user)
    
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from trainer.models import Trainer
from client.models import Client
from nutrition.models import NutritionRequest
from plan.models import Plan
from tickets.models import Ticket
from refund.models import TrainingCancelRequest


class DashboardCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        data = {
            "approved_trainers": Trainer.objects.filter(status="approved").count(),
            "client_count": Client.objects.count(),
            "pending_nutrition_requests": NutritionRequest.objects.filter(status="pending").count(),
            "plan_count": Plan.objects.count(),
            "open_tickets": Ticket.objects.filter(status="open").count(),
            "open_refund_requests": TrainingCancelRequest.objects.filter(status="open").count(),
        }

        return Response(data)




class ClientProfileView(generics.RetrieveAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsUser]

    def get_object(self):
        return Client.objects.get(user=self.request.user)

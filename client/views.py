from rest_framework import generics, permissions
from .models import Client
from .serializers import ClientSerializer
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

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
from rest_framework.parsers import MultiPartParser, FormParser

class ClientCreateView(generics.CreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        print("\n========== RAW REQUEST DEBUG ==========")
        print("CONTENT TYPE:", request.content_type)
        print("REQUEST.DATA:", request.data)
        print("REQUEST.DATA TYPE:", type(request.data))

        print("\n--- INDIVIDUAL FIELDS ---")
        for key, value in request.data.items():
            print(f"{key}: {value} | type: {type(value)}")

        print("\n--- FILES ---")
        print(request.FILES)

        print("=====================================\n")
        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)

        return Response({
            "status": True,
            "message": "Client registered successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)



# List clients (authenticated only)
from django.db.models import Q

class ClientListView(generics.ListAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Client.objects.all()

        search = self.request.query_params.get("search")
        plan = self.request.query_params.get("plan")
        plan_id = self.request.query_params.get("plan_id")

        if search:
            queryset = queryset.filter(name__icontains=search)

        if plan:
            queryset = queryset.filter(
                slotbooking__plan__plan_name__icontains=plan
            ).distinct()

        if plan_id:
            queryset = queryset.filter(
                slotbooking__plan__id=plan_id
            ).distinct()

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "status": True,
            "data": response.data
        }, status=status.HTTP_200_OK)




# Retrieve, Update, Delete client profile (authenticated only)
from django.shortcuts import get_object_or_404

class ClientRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                "status": False,
                "message": "Client not found"
            }, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({
            "status": True,
            "message": "Client updated successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "status": True,
            "message": "Client deleted successfully"
        }, status=status.HTTP_200_OK)




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

            return Response({
                "status": True,
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class ClientProfileView(generics.RetrieveAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsUser]

    def retrieve(self, request, *args, **kwargs):
        try:
            client = get_object_or_404(Client, user=request.user)
            serializer = self.get_serializer(client)
            return Response({
                "status": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                "status": False,
                "message": "Client profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

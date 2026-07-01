from rest_framework import generics, permissions,status
from rest_framework_simplejwt.tokens import RefreshToken
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
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        client = serializer.instance
        user = getattr(client, 'user', None)

        access_token = None
        refresh_token = None

        if user:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

        return Response({
            "status": True,
            "message": "Client registered successfully",
            "data": serializer.data,
            "access": access_token,
            "refresh": refresh_token,
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


from trainer.models import SlotBooking
from .serializers import ClientBookedTrainerSerializer
from django.db.models import Max



class ClientBookedTrainersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = request.user.client

        # 🔹 Get latest booking date per trainer
        latest_booking_ids = (
            SlotBooking.objects
            .filter(client=client)
            .exclude(status__in=["completed", "cancelled", "changed"])
            .values("trainer")
            .annotate(latest_id=Max("id"))
            .values_list("latest_id", flat=True)
        )


        bookings = (
            SlotBooking.objects
            .filter(id__in=latest_booking_ids)
            .select_related("trainer", "plan")
            .order_by("-date")
        )

        serializer = ClientBookedTrainerSerializer(
            bookings,
            many=True,
            context={"request": request}
        )

        return Response({
            "status": True,
            "count": bookings.count(),
            "data": serializer.data
        })
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Client
from .serializers import ClientProfileSerializer1


class ClientPhoneProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response(
                {"status": False, "message": "Client profile not found"},
                status=404
            )

        serializer = ClientProfileSerializer1(
            client,
            context={"request": request}
        )

        return Response({
            "status": True,
            "data": serializer.data
        })
class ClientProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response(
                {"status": False, "message": "Client not found"},
                status=404
            )

        serializer = ClientProfileSerializer1(
            client,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Profile updated successfully",
                "data": serializer.data
            })

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=400)






from .serializers import UnBookedPlanSerializer


class UnBookedPlanListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = request.user.client

        # Get plan IDs for active bookings only.
        # Cancelled or completed trainings should be available again.
        booked_plan_ids = (
            SlotBooking.objects
            .filter(
                client=client,
                status__in=["upcoming", "ongoing", "changed"],
                trainer__status="approved",
            )
            .values_list("plan_id", flat=True)
            .distinct()
        )

        # Exclude currently active plans only
        plans = Plan.objects.exclude(id__in=booked_plan_ids)

        serializer = UnBookedPlanSerializer(
            plans,
            many=True,
            context={"request": request}
        )

        return Response({
            "status": True,
            "data": serializer.data
        })




class ClientBMIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            client = request.user.client
        except Client.DoesNotExist:
            return Response({
                "status": False,
                "message": "Client profile not found"
            }, status=404)

        if not client.weight or not client.height:
            return Response({
                "status": False,
                "message": "Weight and height are required to calculate BMI"
            }, status=400)

        # height in meters
        height_m = float(client.height) / 100
        weight = float(client.weight)

        bmi = round(weight / (height_m * height_m), 2)

        # BMI Category
        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 24.9:
            category = "Normal"
        elif bmi < 29.9:
            category = "Overweight"
        else:
            category = "Obese"

        return Response({
            "status": True,
            "name": client.name,
            "bmi": bmi,
            "category": category
        })

from trainer.models import Payment
from .serializers import ClientPaymentSerializer

class ClientPaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        payments = (
            Payment.objects
            .filter(client_id=client_id, status="success")
            .select_related("trainer", "plan")
            .order_by("-created_at")
        )

        serializer = ClientPaymentSerializer(payments, many=True)
        return Response(serializer.data)

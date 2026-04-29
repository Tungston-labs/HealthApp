from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from accounts.permissions import IsAdmin, IsUser
from .serializers import (
    NutritionRequestCreateSerializer,
    NutritionRequestDetailSerializer,
    NutritionRequestListSerializer
)
from .models import NutritionRequest
from django.core.mail import EmailMessage
from rest_framework import status
from accounts.paginations import CustomPagination


# add request for nutrition

class NutritionRequestCreateView(CreateAPIView):
    serializer_class = NutritionRequestCreateSerializer
    permission_classes = [IsUser]

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
            "message": "Nutrition request submitted successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


# list requests by admin
class AdminNutritionRequestListView(ListAPIView):
    serializer_class = NutritionRequestListSerializer
    permission_classes = [IsAdmin]
    pagination_class = CustomPagination

    def get_queryset(self):
        return (
            NutritionRequest.objects
            .filter(status="pending")
            .select_related("client")
            .order_by("-date")
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        return Response({
            "status": True,
            "data": response.data
        }, status=status.HTTP_200_OK)


# details for admin

class AdminNutritionRequestDetailView(RetrieveAPIView):
    queryset = NutritionRequest.objects.all()
    serializer_class = NutritionRequestDetailSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"

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
                "message": "Nutrition request not found"
            }, status=status.HTTP_404_NOT_FOUND)

# reply to nutrition requests
class AdminNutritionReplyView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, id):
        nutrition_request = get_object_or_404(NutritionRequest, id=id)

        subject = request.data.get("subject")
        message = request.data.get("message")
        files = request.FILES.getlist("files")

        if not subject or not message:
            return Response({
                "status": False,
                "message": "Subject and message are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            email = EmailMessage(
                subject=subject,
                body=message,
                to=[nutrition_request.client.email]
            )

            for f in files:
                email.attach(f.name, f.read(), f.content_type)

            email.send()

        except Exception as e:
            return Response({
                "status": False,
                "message": "Failed to send email",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        nutrition_request.status = "closed"
        nutrition_request.save()

        return Response({
            "status": True,
            "message": "Reply sent and request closed"
        }, status=status.HTTP_200_OK)

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


# add request for nutrition

class NutritionRequestCreateView(CreateAPIView):
    serializer_class = NutritionRequestCreateSerializer
    permission_classes = [IsUser]

# list requests by admin
class AdminNutritionRequestListView(ListAPIView):
    queryset = NutritionRequest.objects.filter(status="pending").order_by("-date")
    serializer_class = NutritionRequestListSerializer
    permission_classes = [IsAdmin]

# details for admin

class AdminNutritionRequestDetailView(RetrieveAPIView):
    queryset = NutritionRequest.objects.all()
    serializer_class = NutritionRequestDetailSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"

# reply to nutrition requests
class AdminNutritionReplyView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, id):
        # --- Get request object safely ---
        nutrition_request = get_object_or_404(NutritionRequest, id=id)

        subject = request.data.get("subject")
        message = request.data.get("message")
        files = request.FILES.getlist("files")

        # --- Validate input ---
        if not subject or not message:
            return Response(
                {"error": "Subject and message are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- Setup email ---
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
            return Response(
                {"error": "Failed to send email", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # --- Update request status ---
        nutrition_request.status = "closed"
        nutrition_request.save()

        return Response(
            {"success": "Reply sent and status updated."},
            status=status.HTTP_200_OK
        )

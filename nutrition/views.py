from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView,Response
from rest_framework.generics import CreateAPIView,ListAPIView,RetrieveAPIView
from accounts.permissions import IsAdmin,IsUser
from .serializers import NutritionRequestCreateSerializer,NutritionRequestDetailSerializer,NutritionRequestListSerializer
from .models import NutritionRequest
from django.core.mail import EmailMessage

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
        try:
            nutrition_request = NutritionRequest.objects.get(id=id)
        except NutritionRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=404)

        subject = request.data.get("subject")
        message = request.data.get("message")
        files = request.FILES.getlist("files")

        if not subject or not message:
            return Response({"error": "Subject & message are required"}, status=400)

        email = EmailMessage(
            subject=subject,
            body=message,
            to=[nutrition_request.client.email]
        )

        for f in files:
            email.attach(f.name, f.read(), f.content_type)

        email.send()

        nutrition_request.status = "closed"
        nutrition_request.save()

        return Response({"success": "Reply sent & status updated"}, status=200)

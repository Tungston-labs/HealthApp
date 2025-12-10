from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Ticket
from .serializers import (
    TicketCreateSerializer, TicketListSerializer,
    TicketDetailSerializer, TicketStatusUpdateSerializer
)
from accounts.permissions import IsAdmin, IsUser
from accounts.paginations import CustomPagination

class TicketCreateView(CreateAPIView):
    serializer_class = TicketCreateSerializer
    permission_classes = [IsUser]

class AdminTicketListView(ListAPIView):
    queryset = Ticket.objects.all().order_by("-date")
    serializer_class = TicketListSerializer
    permission_classes = [IsAdmin]
    pagination_class = CustomPagination


class AdminTicketDetailView(RetrieveAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketDetailSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"

class AdminTicketStatusUpdateView(UpdateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketStatusUpdateSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"

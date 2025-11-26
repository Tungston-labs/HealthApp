from django.urls import path
from .views import (
    TicketCreateView, AdminTicketListView,
    AdminTicketDetailView, AdminTicketStatusUpdateView
)

urlpatterns = [
    path("create/", TicketCreateView.as_view()),
    path("admin/", AdminTicketListView.as_view()),
    path("admin/<int:id>/", AdminTicketDetailView.as_view()),
    path("admin/<int:id>/status/", AdminTicketStatusUpdateView.as_view()),
]

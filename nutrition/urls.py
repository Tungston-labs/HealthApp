# nutrition/urls.py
from django.urls import path
from .views import (
    NutritionRequestCreateView,
    AdminNutritionRequestListView,
    AdminNutritionRequestDetailView,
    AdminNutritionReplyView,
)

urlpatterns = [
    path("request/", NutritionRequestCreateView.as_view()),
    path("admin/", AdminNutritionRequestListView.as_view()),
    path("admin/<int:id>/", AdminNutritionRequestDetailView.as_view()),
    path("admin/<int:id>/reply/", AdminNutritionReplyView.as_view()),
]

# plans/urls.py
from django.urls import path
from .views import PlanListCreateView, PlanRetrieveUpdateDeleteView

urlpatterns = [
    path('', PlanListCreateView.as_view(), name='plan-list-create'),
    path('<int:pk>/', PlanRetrieveUpdateDeleteView.as_view(), name='plan-detail'),
]

# plans/urls.py
from django.urls import path
from .views import PlanListCreateView, PlanRetrieveUpdateDeleteView,PlanListView,PlanDetailView,PlanPendingCountListView,PlanMiniListView

urlpatterns = [
    path('', PlanListCreateView.as_view(), name='plan-list-create'),
    path('<int:pk>/', PlanRetrieveUpdateDeleteView.as_view(), name='plan-detail'),
    path("pending-count/", PlanPendingCountListView.as_view()),
    path('miniplanlist/',PlanMiniListView.as_view()),
        # --------plan list,detail view
    path('clientlist/', PlanListView.as_view(), name='plan-list'),
    path('clientview/<int:pk>/', PlanDetailView.as_view(), name='plan-detail'),

    
]

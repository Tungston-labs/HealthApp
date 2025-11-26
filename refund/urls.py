from django.urls import path
from .views import RequestTrainingCancelView, ClientCancelRequestListView,TrainingCancelListView,TrainingCancelDetailView,TrainingCancelStatusUpdateView

urlpatterns = [
    path("training/cancel/", RequestTrainingCancelView.as_view(), name="training-cancel"),
    path("training/cancel/history/", ClientCancelRequestListView.as_view(), name="cancel-history"),
    path("cancel-requests/", TrainingCancelListView.as_view(), name="cancel-request-list"),
    path("cancel-requests/<int:pk>/", TrainingCancelDetailView.as_view(), name="cancel-request-detail"),
    path("cancel-requests/<int:pk>/status/", TrainingCancelStatusUpdateView.as_view(), name="cancel-request-update-status"),
    
]

from django.urls import path
from .views import TrainerCreateView, TrainerListView, TrainerDetailView,LocalImageUploadAPIView,TrainerProfileView,TrainerProfileEditView,PendingTrainerListView

urlpatterns = [
    path('', TrainerCreateView.as_view(), name='trainer-create'),
    path('list/', TrainerListView.as_view(), name='trainer-list'),
    path('<int:pk>/', TrainerDetailView.as_view(), name='trainer-detail'),
    path('upload-image/', LocalImageUploadAPIView.as_view()),
    path('trainers/pending/', PendingTrainerListView.as_view(), name='pending-trainers'),


# ------MOBILE APP

    path('profile/', TrainerProfileView.as_view(), name='trainer-profile'),
    path('profile/edit/', TrainerProfileEditView.as_view(), name='trainer-profile-edit'),

]

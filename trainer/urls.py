from django.urls import path
from .views import TrainerCreateView, TrainerListView, TrainerDetailView,LocalImageUploadAPIView,TrainerProfileView,TrainerProfileEditView,PendingTrainerListView,FilterTrainersView,BookTrainerView,TrainerDetailPageView,ChangeTrainerView

urlpatterns = [
    path('', TrainerCreateView.as_view(), name='trainer-create'),
    path('list/', TrainerListView.as_view(), name='trainer-list'),
    path('<int:pk>/', TrainerDetailView.as_view(), name='trainer-detail'),
    path('upload-image/', LocalImageUploadAPIView.as_view()),
    path('trainers/pending/', PendingTrainerListView.as_view(), name='pending-trainers'),


# ------MOBILE APP-trainer

    path('profile/', TrainerProfileView.as_view(), name='trainer-profile'),
    path('profile/edit/', TrainerProfileEditView.as_view(), name='trainer-profile-edit'),

# ------MOBILE APP-user

    path("available-trainers/", FilterTrainersView.as_view(), name="available-trainers"),
    path("detail/<int:trainer_id>/", TrainerDetailPageView.as_view()),
    path("book-trainer/", BookTrainerView.as_view(), name="book-trainer"),
    path('change/', ChangeTrainerView.as_view(), name='change-trainer'),

]

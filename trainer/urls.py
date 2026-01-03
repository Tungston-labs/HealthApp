from django.urls import path
from .views import TrainerCreateView, TrainerListView, TrainerDetailView,LocalImageUploadAPIView,TrainerProfileView,TrainerProfileEditView,PendingTrainerListView,FilterTrainersView,BookTrainerView,TrainerDetailPageView,ChangeTrainerView,TrainerDetailSimpleView,AddSlotBookingNoteView,SuspendTrainerView,TrainerPendingListView,SlotBookingNoteDetailView,DeleteSlotBookingNoteView,OngoingSessionView,VerifyPaymentAndCreateBookingView,TrainerClientsListView

urlpatterns = [
    path('', TrainerCreateView.as_view(), name='trainer-create'),
    path('list/', TrainerListView.as_view(), name='trainer-list'),
    path('pending-request/', TrainerPendingListView.as_view(), name='pending-list'),

    path('<int:pk>/', TrainerDetailView.as_view(), name='trainer-detail'),
    path('upload-image/', LocalImageUploadAPIView.as_view()),
    path("trainers/pending/<int:plan_id>/",PendingTrainerListView.as_view(),name="pending-trainers-by-plan",),
    path(
        "<int:trainer_id>/suspend/",
        SuspendTrainerView.as_view(),
        name="suspend-trainer"
    ),


# ------MOBILE APP-trainer

    path('profile/', TrainerProfileView.as_view(), name='trainer-profile'),
    path('profile/edit/', TrainerProfileEditView.as_view(), name='trainer-profile-edit'),
    path('ongoing-sessions/', OngoingSessionView.as_view(), name='trainer-ongoing-sessions'),
    path('assigned-clients/' ,TrainerClientsListView.as_view(),name='trainer-client'),

# ------MOBILE APP-user

    path("available-trainers/", FilterTrainersView.as_view(), name="available-trainers"),
    path("detail/<int:trainer_id>/", TrainerDetailPageView.as_view()),
    path("book-trainer/", BookTrainerView.as_view(), name="book-trainer"),

    path('change/', ChangeTrainerView.as_view(), name='change-trainer'),
    path('info/<int:trainer_id>/', TrainerDetailSimpleView.as_view(), name='trainer-detail-simple'),
    path('booking/<int:booking_id>/add-note/', AddSlotBookingNoteView.as_view(), name='add-slot-note'),
    path("booking/<int:booking_id>/note/",SlotBookingNoteDetailView.as_view(),name="get-slot-booking-note"),
    path("bookings/<int:booking_id>/notes/delete/<int:index>/",DeleteSlotBookingNoteView.as_view()),



]

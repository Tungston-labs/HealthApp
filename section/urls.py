from django.urls import path
from .views import TrainerTodaySessionsView,ClientDetailView,TrainerAllBookingsView,TrainerHistorySessionsView,StartTrainingView,EndTrainingView,ClientCompletedSessionsView,ClientSessionDetailView

urlpatterns = [
path("today-sessions/", TrainerTodaySessionsView.as_view()),
path("client/<int:client_id>/", ClientDetailView.as_view()),
path("trainer/bookings/", TrainerAllBookingsView.as_view()),        # upcoming / all
path("trainer/history/", TrainerHistorySessionsView.as_view()),      # completed
path('start-training/', StartTrainingView.as_view(), name='start-training'),
path('end-training/', EndTrainingView.as_view(), name='end-training'),
path('client/completed-sessions/', ClientCompletedSessionsView.as_view(), name='client-completed-sessions'),
path('client/completed-session/<int:session_id>/', ClientSessionDetailView.as_view(), name='client-session-detail'),
]
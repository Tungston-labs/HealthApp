from django.urls import path
from .views import ClientCreateView, ClientListView, ClientRetrieveUpdateDeleteView,ClientProfileView,DashboardCountView,ClientBookedTrainersView

urlpatterns = [
    path('register/', ClientCreateView.as_view(), name='client-register'),
    path('', ClientListView.as_view(), name='client-list'),
    path('<int:pk>/', ClientRetrieveUpdateDeleteView.as_view(), name='client-detail'),
    path('profile/', ClientProfileView.as_view(), name='client-profile'),
    path("dashboard/counts/", DashboardCountView.as_view()),
    path("booked-trainers/", ClientBookedTrainersView.as_view()),


]

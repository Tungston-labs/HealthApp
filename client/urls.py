from django.urls import path
from .views import ClientCreateView, ClientListView, ClientRetrieveUpdateDeleteView,ClientProfileView,DashboardCountView,ClientBookedTrainersView,ClientPhoneProfileView,ClientProfileUpdateView,UnBookedPlanListView

urlpatterns = [
    path('register/', ClientCreateView.as_view(), name='client-register'),
    path('', ClientListView.as_view(), name='client-list'),
    path('<int:pk>/', ClientRetrieveUpdateDeleteView.as_view(), name='client-detail'),
    path('profile/', ClientProfileView.as_view(), name='client-profile'),
    path("dashboard/counts/", DashboardCountView.as_view()),
    path("booked-trainers/", ClientBookedTrainersView.as_view()),
    path("mob/profile/", ClientPhoneProfileView.as_view()),
    path("profile/edit/", ClientProfileUpdateView.as_view()),
    path("plans/unbooked/", UnBookedPlanListView.as_view()),


]

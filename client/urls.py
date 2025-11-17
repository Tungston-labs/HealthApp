from django.urls import path
from .views import ClientCreateView, ClientListView, ClientRetrieveUpdateDeleteView

urlpatterns = [
    path('register/', ClientCreateView.as_view(), name='client-register'),
    path('', ClientListView.as_view(), name='client-list'),
    path('<int:pk>/', ClientRetrieveUpdateDeleteView.as_view(), name='client-detail'),


]

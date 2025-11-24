from django.urls import path
from .views import TrainerReviewCreateView

urlpatterns = [
    path('trainer-review/', TrainerReviewCreateView.as_view(), name='trainer-review'),
]

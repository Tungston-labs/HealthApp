from django.urls import path
from .views import (
    LoginAPIView, LogoutAPIView,
    ForgotPasswordStep1APIView, VerifyOTPAPIView,
    ResetPasswordAPIView, ChangePasswordAPIView
)

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("forgot-password/step1/", ForgotPasswordStep1APIView.as_view(), name="forgot-password-step1"),
    path("forgot-password/verify-otp/", VerifyOTPAPIView.as_view(), name="verify-otp"),
    path("forgot-password/reset/", ResetPasswordAPIView.as_view(), name="reset-password"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
]

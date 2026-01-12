from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    LoginSerializer, ForgotPasswordStep1Serializer,
    VerifyOTPSerializer, ResetPasswordSerializer,
    ChangePasswordSerializer
)
from django.core.exceptions import ValidationError
# ---------------- LOGIN ---------------- #
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from trainer.models import SlotBooking

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from trainer.models import SlotBooking
from trainer.models import Trainer


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            # -------------------------------
            # DEFAULT VALUES
            # -------------------------------
            has_session = False
            trainer_data = None

            # -------------------------------
            # NORMAL USER → SESSION CHECK
            # -------------------------------
            if user.role == "user":
                try:
                    client = user.client  # OneToOne
                    has_session = SlotBooking.objects.filter(
                        client=client,
                        status__in=["upcoming", "ongoing"]
                    ).exists()
                except Exception:
                    has_session = False

            # -------------------------------
            # TRAINER → PLAN DETAILS
            # -------------------------------
            if user.role == "trainer":
                try:
                    trainer = Trainer.objects.select_related("training_field").get(user=user)

                    trainer_data = {
                        "trainer_id": trainer.id,
                        "trainer_name": trainer.name,
                        "status": trainer.status,
                        "training_plan": {
                            "id": trainer.training_field.id if trainer.training_field else None,
                            "name": trainer.training_field.name if trainer.training_field else None,
                        }
                    }
                except Trainer.DoesNotExist:
                    trainer_data = None

            # -------------------------------
            # RESPONSE
            # -------------------------------
            return Response({
                "status": True,
                "message": "Login successful",
                "data": {
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "role": user.role,
                        "session": has_session,        # for users
                        "trainer": trainer_data        # for trainers
                    },
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                "status": False,
                "message": "Login failed",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)


# ---------------- LOGOUT ---------------- #
class LogoutAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                "status": True,
                "message": "Logged out successfully"
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({
                "status": False,
                "message": "Invalid refresh token"
            }, status=status.HTTP_400_BAD_REQUEST)


# ---------------- FORGOT PASSWORD STEP1 ---------------- #
class ForgotPasswordStep1APIView(generics.GenericAPIView):
    serializer_class = ForgotPasswordStep1Serializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                "status": True,
                "message": "OTP sent to email"
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                "status": False,
                "message": "Failed to send OTP",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)


# ---------------- VERIFY OTP ---------------- #
class VerifyOTPAPIView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

            return Response({
                "status": True,
                "message": "OTP verified"
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                "status": False,
                "message": "Invalid OTP",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)


# ---------------- RESET PASSWORD ---------------- #
class ResetPasswordAPIView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                "status": True,
                "message": "Password reset successfully"
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                "status": False,
                "message": "Password reset failed",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)


# ---------------- CHANGE PASSWORD ---------------- #
class ChangePasswordAPIView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )

        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                "status": True,
                "message": "Password changed successfully"
            }, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({
                "status": False,
                "message": "Password change failed",
                "errors": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

class RefreshAccessTokenAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({
                "status": False,
                "message": "Refresh token is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)

            return Response({
                "status": True,
                "message": "Access token refreshed successfully",
                "data": {
                    "access": str(refresh.access_token)
                }
            }, status=status.HTTP_200_OK)

        except (TokenError, InvalidToken):
            return Response({
                "status": False,
                "message": "Invalid or expired refresh token"
            }, status=status.HTTP_401_UNAUTHORIZED)

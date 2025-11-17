from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, OTP
import random
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

# ---------------- LOGIN ---------------- #
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email_or_phno = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email_or_phno = attrs.get("email_or_phno")
        password = attrs.get("password")

        # Check for email OR phone number
        user = User.objects.filter(Q(email=email_or_phno) |Q(phno=email_or_phno)).first()

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        attrs["user"] = user
        return attrs




# ---------------- FORGOT PASSWORD STEP1: SEND OTP ---------------- #
class ForgotPasswordStep1Serializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist")
        return value

    def save(self):
        email = self.validated_data['email']
        otp = str(random.randint(100000, 999999))
        OTP.objects.update_or_create(email=email, defaults={"otp": otp})
        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        return otp

# ---------------- FORGOT PASSWORD STEP2: VERIFY OTP ---------------- #
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")
        if not OTP.objects.filter(email=email, otp=otp).exists():
            raise serializers.ValidationError("Invalid OTP")
        return attrs

# ---------------- FORGOT PASSWORD STEP3: RESET PASSWORD ---------------- #
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")
        validate_password(password)
        return attrs

    def save(self):
        email = self.validated_data['email']
        password = self.validated_data['password']
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()
        OTP.objects.filter(email=email).delete()
        return user

# ---------------- CHANGE PASSWORD ---------------- #
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("confirm_new_password"):
            raise serializers.ValidationError("New passwords do not match")
        validate_password(attrs.get("new_password"))
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

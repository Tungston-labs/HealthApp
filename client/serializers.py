from rest_framework import serializers
from .models import Client
from accounts.models import User
import datetime
from decimal import Decimal
from rest_framework import serializers
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()

class ClientSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    profile_pic = serializers.ImageField(required=False)
    plan_names = serializers.SerializerMethodField(read_only=True)

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['user']

    # ---------------- VALIDATIONS ----------------
    def validate_email(self, value):
        if Client.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_phno(self, value):
        if Client.objects.filter(phno=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value

    def get_plan_names(self, obj):
        return list(
            obj.slotbooking_set
            .select_related("plan")
            .values_list("plan__plan_name", flat=True)
            .distinct()
        )

    def create(self, validated_data):
        password = validated_data.pop('password')

        latitude = validated_data.get("latitude")
        longitude = validated_data.get("longitude")

        if latitude is not None:
            validated_data["latitude"] = Decimal(latitude)

        if longitude is not None:
            validated_data["longitude"] = Decimal(longitude)

        client = Client.objects.create(**validated_data)

        user = User.objects.create_user(
            email=client.email,
            phno=client.phno,
            password=password,
            role='user',
            name=client.name
        )

        client.user = user
        client.save()

        return client



from rest_framework import serializers
from client.models import Client
from trainer.models import SlotBooking

class TrainerSessionSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = SlotBooking
        fields = ['trainer_name', 'profile_pic', 'day_name', 'time', 'date']

    trainer_name = serializers.CharField(source='trainer.name', read_only=True)

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if obj.trainer.profile_pic:
            return request.build_absolute_uri(obj.trainer.profile_pic.url)
        return None

    def get_day_name(self, obj):
        return obj.date.strftime("%A")  # Monday, Tuesday, etc.
        

class ClientProfileSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    bmi = serializers.SerializerMethodField()
    upcoming_sessions = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['name', 'profile_pic', 'bmi', 'upcoming_sessions']

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    def get_bmi(self, obj):
        if obj.height and obj.weight:
            # BMI = weight(kg) / (height(m))^2
            return round(float(obj.weight) / ((float(obj.height)/100)**2), 2)
        return None

    def get_upcoming_sessions(self, obj):
        today = datetime.date.today()
        sessions = SlotBooking.objects.filter(client=obj, date__gte=today).order_by('date', 'time')
        return TrainerSessionSerializer(sessions, many=True, context=self.context).data
    
from trainer.models import SlotBooking

class ClientBookedTrainerSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    trainer_id = serializers.CharField(source="trainer.id", read_only=True)
    trainer_profile_pic = serializers.SerializerMethodField()
    plan_name = serializers.CharField(source="plan.plan_name", read_only=True)
    day = serializers.SerializerMethodField()

    class Meta:
        model = SlotBooking
        fields = [
            "id",
            "trainer_name",
            "trainer_id",
            "trainer_profile_pic",
            "plan_name",
            "date",
            "day",
            "time",
            "status",
        ]

    def get_trainer_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.trainer.profile_pic:
            return request.build_absolute_uri(obj.trainer.profile_pic.url)
        return None

    def get_day(self, obj):
        return obj.date.strftime("%A")
from rest_framework import serializers
from .models import Client


class ClientProfileSerializer1(serializers.ModelSerializer):
    profile_pic_url = serializers.SerializerMethodField()

    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )

    name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phno = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "phno",
            "email",
            "dob",
            "gender",
            "blood_group",
            "weight",
            "height",
            "address",
            "latitude",
            "longitude",
            "profile_pic",
            "profile_pic_url",
            "health_issues",
            "wellness_goal",
        ]
        read_only_fields = ["id"]

    def get_profile_pic_url(self, obj):
        request = self.context.get("request")
        if obj.profile_pic and request:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    def update(self, instance, validated_data):
        user = instance.user

        # -------------------------
        # 1. Update CLIENT model
        # -------------------------
        client_fields = [
            'name', 'email', 'phno',
            'dob', 'gender', 'blood_group',
            'weight', 'height', 'address',
            'latitude', 'longitude',
            'health_issues', 'wellness_goal',
            'profile_pic'
        ]

        for field in client_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()

        # -------------------------
        # 2. Update USER model
        # -------------------------
        if user:
            user_fields = ['name', 'email', 'phno']
            for field in user_fields:
                if field in validated_data:
                    setattr(user, field, validated_data[field])
            user.save()

        return instance




from plan.models import Plan


class UnBookedPlanSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        source="single_price",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Plan
        fields = [
            "id",
            "plan_name",
            "plan_type",
            "image",
            "amount",
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.upload_file and request:
            return request.build_absolute_uri(obj.upload_file.url)
        return None



from trainer.models import Payment

class ClientPaymentSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    plan_name = serializers.CharField(source="plan.plan_name", read_only=True)
    paid_date = serializers.DateTimeField(source="created_at", read_only=True,format="%d-%m-%Y %H:%M")

    class Meta:
        model = Payment
        fields = [
            "id",
            "trainer_name",
            "plan_name",
            "razorpay_payment_id",
            "paid_date",
            "amount",
            "status",
        ]

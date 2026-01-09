from rest_framework import serializers
from .models import Client
from accounts.models import User
import datetime
class ClientSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    profile_pic = serializers.ImageField(required=False)
    plan_names = serializers.SerializerMethodField(read_only=True)  

    class Meta:
        model = Client
        fields = '__all__'   # plan_names will be auto included
        read_only_fields = ['user']

    def get_plan_names(self, obj):
        """
        Returns all distinct plan names this client belongs to
        """
        return list(
            obj.slotbooking_set
            .select_related("plan")
            .values_list("plan__plan_name", flat=True)
            .distinct()
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.get('email')
        phno = validated_data.get('phno')

        # Create Client
        client = Client.objects.create(**validated_data)

        # Create User
        user = User.objects.create_user(
            email=email,
            phno=phno,
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
    trainer_profile_pic = serializers.SerializerMethodField()
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    day = serializers.SerializerMethodField()

    class Meta:
        model = SlotBooking
        fields = [
            "id",
            "trainer_name",
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
            "profile_pic",
            "profile_pic_url",
            "health_issues",
            "wellness_goal",
        ]
        read_only_fields = ["id", "phno", "email"]

    def get_profile_pic_url(self, obj):
        request = self.context.get("request")
        if obj.profile_pic and request:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

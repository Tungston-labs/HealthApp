import json
from rest_framework import serializers
from .models import Client
from accounts.models import User

class ClientSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    profile_pic = serializers.ImageField(required=False)
    health_issues = serializers.ListField(
    child=serializers.CharField(),
    required=False
     )

    wellness_goal = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


    class Meta:
        model = Client
        fields = [
            "name", "email", "phno", "password",
            "dob", "gender", "blood_group",
            "height", "weight", "address",
            "health_issues", "wellness_goal",
            "profile_pic",
        ]

    def to_internal_value(self, data):
        data = data.copy()

        for field in ["health_issues", "wellness_goal"]:
            value = data.get(field)

            # Handle list-wrapped values from multipart
            if isinstance(value, list):
                value = value[0]

            if isinstance(value, str):
                try:
                    data[field] = json.loads(value)
                except Exception:
                    data[field] = []

        return super().to_internal_value(data)


    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.pop("email")
        phno = validated_data.pop("phno")

        client = Client.objects.create(**validated_data)

        user = User.objects.create_user(
            email=email,
            phno=phno,
            password=password,
            role="user",
            name=client.name,
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

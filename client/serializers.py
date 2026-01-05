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

    import json

    def create(self, validated_data):
        # Required for User
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        phno = validated_data.pop('phno')

        # Remove fields not in Client model
        validated_data.pop('role', None)

        # Parse JSON string fields safely
        health_issues = validated_data.pop('health_issues', '[]')
        wellness_goal = validated_data.pop('wellness_goal', '[]')

        try:
            health_issues = json.loads(health_issues)
        except Exception:
            health_issues = []

        try:
            wellness_goal = json.loads(wellness_goal)
        except Exception:
            wellness_goal = []

        # Create Client
        client = Client.objects.create(
            email=email,
            phno=phno,
            health_issues=health_issues,
            wellness_goal=wellness_goal,
            **validated_data
        )

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

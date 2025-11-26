from rest_framework import serializers
from trainer.models import SlotBooking
from client.models import Client
from datetime import date
class ClientMiniSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ["id", "name", "profile_pic", "height", "weight", "blood_group", "address"]

    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

class TodaySessionSerializer(serializers.ModelSerializer):
    client = ClientMiniSerializer()

    class Meta:
        model = SlotBooking
        fields = ["date", "time", "client"]
class ClientDetailSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    upcoming_sessions = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id", "name", "email", "gender", "blood_group", "weight", "height",
            "wellness_goal", "health_issues", "address",
            "profile_pic", "upcoming_sessions"
        ]

    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    def get_upcoming_sessions(self, obj):
        from trainer.models import SlotBooking
        upcoming = SlotBooking.objects.filter(
            client=obj,
            date__gte=date.today()
        ).order_by("date", "time")

        return [
            {
                "date": s.date,
                "time": s.time,
                "trainer_name": s.trainer.name,
                "section_timing": s.trainer.section_timing  # <-- added this
            }
            for s in upcoming
        ]



# for all session  details
from rest_framework import serializers
from client.models import Client
from trainer.models import SlotBooking

class BookingClientSerializer(serializers.ModelSerializer):
    profile_pic_url = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ["id", "name", "height", "weight", "blood_group", "address", "profile_pic_url"]

    def get_profile_pic_url(self, obj):
        request = self.context.get("request")
        if obj.profile_pic and request:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None


class AllBookingSerializer(serializers.ModelSerializer):
    client = BookingClientSerializer()
    time_label = serializers.SerializerMethodField()

    class Meta:
        model = SlotBooking
        fields = [
            "id",
            "date",
            "time",
            "time_label",
            "session_end_date",
            "session_end_time",
            "status",
            "client"
        ]

    def get_time_label(self, obj):
        h = obj.time.hour
        if 5 <= h < 12:
            return "morning"
        elif 12 <= h < 17:
            return "noon"
        else:
            return "evening"


# for getting already done session details
from rest_framework import serializers
from trainer.models import SlotBooking

class HistoryBookingSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_profile_pic = serializers.SerializerMethodField()
    client_id = serializers.IntegerField(source='client.id', read_only=True)
    client_height = serializers.DecimalField(source='client.height', max_digits=5, decimal_places=2, read_only=True)
    client_weight = serializers.DecimalField(source='client.weight', max_digits=5, decimal_places=2, read_only=True)
    client_blood_group = serializers.CharField(source='client.blood_group', read_only=True)
    client_location = serializers.CharField(source='client.address', read_only=True)

    session_end_date = serializers.DateField(read_only=True)
    session_end_time = serializers.TimeField(read_only=True)

    class Meta:
        model = SlotBooking
        fields = [
            'id',
            'date',
            'time',
            'plan',
            'status',
            'session_end_date',
            'session_end_time',
            'client_id',
            'client_name',
            'client_profile_pic',
            'client_height',
            'client_weight',
            'client_blood_group',
            'client_location',
        ]

    def get_client_profile_pic(self, obj):
        request = self.context.get('request')
        if obj.client.profile_pic and request:
            return request.build_absolute_uri(obj.client.profile_pic.url)
        return None

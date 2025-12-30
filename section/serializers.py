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
        fields = ["date", "time", "client","id"]
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
    session_number = serializers.SerializerMethodField()
    total_sessions = serializers.SerializerMethodField()

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
            "client",
            "session_number",
            "total_sessions",
        ]

    def get_time_label(self, obj):
        h = obj.time.hour
        if 5 <= h < 12:
            return "morning"
        elif 12 <= h < 17:
            return "noon"
        else:
            return "evening"

    def get_total_sessions(self, obj):
        # total sessions from trainer profile
        return obj.trainer.no_of_section

    def get_session_number(self, obj):
        """
        Calculate session index using date + time order
        """
        bookings = SlotBooking.objects.filter(
            trainer=obj.trainer,
            client=obj.client,
            plan=obj.plan,
        ).order_by("date", "time")

        booking_ids = list(bookings.values_list("id", flat=True))

        try:
            return booking_ids.index(obj.id) + 1
        except ValueError:
            return 1

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



class ClientSessionHistorySerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    start_date = serializers.DateField(source="date", read_only=True)

    session_period = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()

    class Meta:
        model = SlotBooking
        fields = [
            "trainer_name",
            "session_period",
            "start_date",
            "end_date",
            "amount",
        ]

    def get_session_period(self, obj):
        plan_type = obj.plan.plan_type
        if plan_type == "3_days":
            return "3 Days"
        if plan_type == "6_days":
            return "6 Days"
        return "Unknown"

    def get_end_date(self, obj):
        return obj.session_end_date or obj.date

    def get_amount(self, obj):
        plan = obj.plan
        if plan.plan_type == "3_days":
            return plan.single_price
        if plan.plan_type == "6_days":
            return plan.couple_price
        return plan.single_price






class AdminTrainerSessionSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    trainer_profile = serializers.SerializerMethodField()
    session_period = serializers.SerializerMethodField()
    start_date = serializers.DateField(source="date")
    end_date = serializers.DateField(source="session_end_date")
    amount = serializers.DecimalField(
        source="plan.price",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = SlotBooking
        fields = [
            "id",
            "trainer_name",
            "trainer_profile",
            "session_period",
            "start_date",
            "end_date",
            "amount",
            "status",
        ]

    def get_trainer_profile(self, obj):
        request = self.context.get("request")
        if obj.trainer.profile_pic and request:
            return request.build_absolute_uri(obj.trainer.profile_pic.url)
        return None

    def get_session_period(self, obj):
        # Example: "3 weeks / 4 weeks"
        duration = getattr(obj.plan, "duration_weeks", None)
        if duration:
            return f"{duration} weeks"
        return "-"

from plan.models import Plan
class ClientDetailSerializer(serializers.ModelSerializer):
    profile_pic_url = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "email",
            "phno",
            "gender",
            "blood_group",
            "height",
            "weight",
            "address",
            "health_issues",
            "wellness_goal",
            "profile_pic_url",
        ]

    def get_profile_pic_url(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None
class PlanDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id",
            "plan_name",
            "plan_type",
            "description",
        ]


from datetime import datetime, timedelta

class SlotBookingDetailSerializer(serializers.ModelSerializer):
    client = ClientDetailSerializer()
    plan = PlanDetailSerializer()

    session_number = serializers.SerializerMethodField()
    total_sessions = serializers.SerializerMethodField()
    training_time = serializers.SerializerMethodField()

    class Meta:
        model = SlotBooking
        fields = [
            "id",
            "status",
            "date",
            "time",
            "session_end_date",
            "session_end_time",
            "training_time",
            "session_number",
            "total_sessions",
            "client",
            "plan",
            "notes",
        ]

    def get_total_sessions(self, obj):
        return obj.trainer.no_of_section

    def get_session_number(self, obj):
        sessions = SlotBooking.objects.filter(
            trainer=obj.trainer,
            client=obj.client,
            plan=obj.plan
        ).order_by("date", "time")

        for index, session in enumerate(sessions, start=1):
            if session.id == obj.id:
                return index
        return None

    def get_training_time(self, obj):
        start_time = obj.time
        duration = int(obj.trainer.section_timing)

        end_time = (
            datetime.combine(obj.date, start_time)
            + timedelta(minutes=duration)
        ).time()

        return {
            "start": start_time.strftime("%H:%M"),
            "end": end_time.strftime("%H:%M"),
            "duration_minutes": duration
        }

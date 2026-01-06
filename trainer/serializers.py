from rest_framework import serializers
from .models import Trainer, TrainerCertificate,TrainerAvailability,SlotBooking
from rest_framework import serializers
from client.models import Client
from review.models import TrainerReview
import json

class TrainerAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerAvailability
        fields = "__all__"


class TrainerCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerCertificate
        fields = ['id', 'image_url']

from rest_framework import serializers
from .models import Trainer, TrainerCertificate
from plan.models import Plan


class TrainerSerializer(serializers.ModelSerializer):
    certificates = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    certificates_read = serializers.SerializerMethodField()

    password = serializers.CharField(write_only=True, required=False)

    profile_pic = serializers.ImageField(required=False, allow_null=True)
    profile_pic_url = serializers.SerializerMethodField()

    plan_id = serializers.IntegerField(
        source='training_field.id',
        read_only=True
    )
    plan_name = serializers.CharField(
        source='training_field.plan_name',
        read_only=True
    )

    plan_image = serializers.SerializerMethodField()

    class Meta:
        model = Trainer
        fields = '__all__'
        read_only_fields = ['user']

    def get_profile_pic_url(self, obj):
        request = self.context.get("request")
        if obj.profile_pic and request:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None



    def create(self, validated_data):
        request = self.context.get("request")

        # READ certificates[] properly
        certificate_urls = request.data.getlist("certificates[]")

        password = validated_data.pop('password', None)

        trainer = Trainer.objects.create(
            **validated_data,
            password=password
        )

        for url in certificate_urls:
            if url:
                cert = TrainerCertificate.objects.create(image_url=url)
                trainer.certificates.add(cert)

        return trainer




    def get_certificates_read(self, obj):
        request = self.context.get("request")
        return [
            c.image_url if c.image_url.startswith("http")
            else request.build_absolute_uri(c.image_url)
            for c in obj.certificates.all()
        ]
    
    def get_plan_image(self, obj):
        request = self.context.get("request")

        if obj.training_field and obj.training_field.upload_file:
            return request.build_absolute_uri(
                obj.training_field.upload_file.url
            )
        return None
    
    def validate_email(self, value):
        print("EMAIL RECEIVED:", repr(value))
        return value







class TrainerMiniSerializer(serializers.ModelSerializer):
    star_rating = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    single_price = serializers.SerializerMethodField()
    couple_price = serializers.SerializerMethodField()
    group_price = serializers.SerializerMethodField()
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = Trainer
        fields = [
            "id",
            "name",
            "profile_pic",
            "location",
            "experience",
            "star_rating",
            "single_price",
            "couple_price",
            "group_price",
        ]

    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    def get_star_rating(self, obj):
        reviews = getattr(obj, "reviews", None)
        if not reviews:
            return 0
        review_list = reviews.all()  # ← convert RelatedManager to queryset
        if not review_list.exists():
            return 0
        return round(sum(r.rating for r in review_list) / review_list.count(), 1)

    def get_experience(self, obj):
        return getattr(obj, "experience", None)

    def get_single_price(self, obj):
        plan = self.context.get("plan")
        return getattr(plan, "single_price", None)

    def get_couple_price(self, obj):
        plan = self.context.get("plan")
        return getattr(plan, "couple_price", None)

    def get_group_price(self, obj):
        plan = self.context.get("plan")
        return getattr(plan, "group_price", None)

  

# serializer for getting trainer details in mobile app


class TrainerReviewSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.user.name", read_only=True)

    class Meta:
        model = TrainerReview
        fields = ["rating", "review", "client_name", "created_at"]

class TrainerDetailSerializer(serializers.ModelSerializer):
    certificates = serializers.SerializerMethodField()
    profile_pic = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    rating_breakdown = serializers.SerializerMethodField()
    plan_name = serializers.CharField(
        source="training_field.plan_name",
        read_only=True
    )

    class Meta:
        model = Trainer
        fields = [
            "id",
            "name",
            "section_timing",
            "no_of_section",
            "profile_pic",
            "experience",
            "location",
            "certificates",
            "total_reviews",
            "average_rating",
            "rating_breakdown",
            "reviews",
            "plan_name",
        ]

    # Trainer profile pic (full URL)
    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    # Certificate URLs (full URL)
    def get_certificates(self, obj):
        request = self.context.get("request")
        return [
            request.build_absolute_uri(c.image_url)
            for c in obj.certificates.all()
        ]

    # Total reviews
    def get_total_reviews(self, obj):
        return obj.reviews.count()

    # Average rating
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews.exists():
            return 0
        avg = sum(r.rating for r in reviews) / reviews.count()
        return round(avg, 1)

    # Count of 1–5 star ratings
    def get_rating_breakdown(self, obj):
        breakdown = {i: 0 for i in range(1, 6)}
        for r in obj.reviews.all():
            breakdown[r.rating] += 1
        return breakdown

    #  Pass context to nested serializer
    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep["reviews"] = TrainerReviewSerializer(
            instance.reviews.all(),
            many=True,
            context=self.context
        ).data

        return rep

from rest_framework import serializers
from trainer.models import Trainer

class ChangeTrainerSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    star_rating = serializers.SerializerMethodField()
    price = serializers.DecimalField(source="expecting_salary", max_digits=10, decimal_places=2)

    class Meta:
        model = Trainer
        fields = ["id", "name", "profile_pic", "experience", "star_rating", "price", "location"]

    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic and request:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    def get_star_rating(self, obj):
        reviews = getattr(obj, "reviews", None)
        if not reviews or not reviews.exists():
            return 0
        return round(sum(r.rating for r in reviews.all()) / reviews.count(), 1)

class TrainerInfoSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Trainer
        fields = [
            "id",
            "name",
            "location",
            "experience",
            "profile_pic",
            "average_rating",
        ]

    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    def get_average_rating(self, obj):
        from django.db.models import Avg
        avg = TrainerReview.objects.filter(trainer=obj).aggregate(avg=Avg("rating"))["avg"]
        return round(avg, 1) if avg else 0





class SlotBookingNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotBooking
        fields = ["id", "notes"]  # Assuming you add a `note` field to SlotBooking



from rest_framework import serializers
from .models import TrainerPayment

class TrainerPaymentSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)

    class Meta:
        model = TrainerPayment
        fields = "__all__"
        read_only_fields = ("paid_date",)


from rest_framework import serializers
from datetime import datetime, timedelta

class OngoingSessionSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source="id")
    session_start_time = serializers.TimeField(source="time")
    session_duration = serializers.SerializerMethodField()
    session_end_time = serializers.SerializerMethodField()

    class Meta:
        model = SlotBooking
        fields = [
            "session_id",
            "date",
            "session_start_time",
            "session_duration",
            "session_end_time",
            "session_start_apihit_time",
        ]

    def get_session_duration(self, obj):
        """
        From Trainer.section_timing
        """
        return {
            "value": obj.trainer.section_timing,
            "label": obj.trainer.get_section_timing_display()
        }

    def get_session_end_time(self, obj):
        """
        Calculate end time dynamically
        """
        start_dt = datetime.combine(obj.date, obj.time)
        minutes = int(obj.trainer.section_timing)
        end_dt = start_dt + timedelta(minutes=minutes)
        return end_dt.time()



class TrainerClientSessionSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source="id")
    session_time = serializers.TimeField(source="time")

    client_name = serializers.CharField(source="client.name")
    client_weight = serializers.DecimalField(
        source="client.weight",
        max_digits=5,
        decimal_places=2
    )
    client_height = serializers.DecimalField(
        source="client.height",
        max_digits=5,
        decimal_places=2
    )
    client_profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = SlotBooking
        fields = [
            "session_id",
            "date",
            "session_time",
            "status",
            "client_name",
            "client_profile_pic",
            "client_weight",
            "client_height",
        ]

    def get_client_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.client.profile_pic:
            return request.build_absolute_uri(obj.client.profile_pic.url)
        return None

from rest_framework import serializers
from .models import Trainer, TrainerCertificate,TrainerAvailability,SlotBooking
from rest_framework import serializers
from client.models import Client
from health.upload_fields import ImageUploadField
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

from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
import json

from .models import Trainer, TrainerCertificate
User = get_user_model()


class TrainerSerializer(serializers.ModelSerializer):
    # -------------------------
    # WRITE-ONLY INPUTS
    # -------------------------
    certificates = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    password = serializers.CharField(write_only=True, required=False)

    # -------------------------
    # READ-ONLY / COMPUTED
    # -------------------------
    certificates_read = serializers.SerializerMethodField()

    profile_pic = ImageUploadField(required=False, allow_null=True)
    profile_pic_url = serializers.SerializerMethodField()

    plan_id = serializers.IntegerField(
        source="training_field.id",
        read_only=True
    )
    plan_name = serializers.CharField(
        source="training_field.plan_name",
        read_only=True
    )

    plan_image = serializers.SerializerMethodField()

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
        model = Trainer
        fields = "__all__"
        read_only_fields = ["user"]

    # =====================================================
    # VALIDATIONS (EMAIL & PHONE)
    # =====================================================
    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)

        # Ignore self on update
        if self.instance and self.instance.user:
            qs = qs.exclude(id=self.instance.user.id)

        if qs.exists():
            raise serializers.ValidationError("Email already exists")

        return value

    def validate_phno(self, value):
        qs = User.objects.filter(phno=value)

        if self.instance and self.instance.user:
            qs = qs.exclude(id=self.instance.user.id)

        if qs.exists():
            raise serializers.ValidationError("Phone number already exists")

        return value

    # =====================================================
    # CREATE
    # =====================================================
    def _pop_certificate_urls(self, validated_data):
        certificate_urls = validated_data.pop("certificates", None)
        request = self.context.get("request")

        if request is not None and hasattr(request.data, "getlist"):
            multipart_urls = request.data.getlist("certificates[]")
            if multipart_urls:
                certificate_urls = multipart_urls

        if certificate_urls is None:
            return []

        if isinstance(certificate_urls, str):
            try:
                certificate_urls = json.loads(certificate_urls)
            except Exception:
                certificate_urls = [certificate_urls]

        return certificate_urls

    def create(self, validated_data):
        certificate_urls = self._pop_certificate_urls(validated_data)

        password = validated_data.pop("password", None)

        # Normalize lat/lng
        if validated_data.get("latitude") is not None:
            validated_data["latitude"] = Decimal(validated_data["latitude"])
        if validated_data.get("longitude") is not None:
            validated_data["longitude"] = Decimal(validated_data["longitude"])

        # Create Trainer
        trainer = Trainer.objects.create(**validated_data)

        # Create linked User
        if password:
            user = User.objects.create_user(
                email=trainer.email,
                phno=trainer.phno,
                password=password,
                role="trainer",
                name=trainer.name
            )
            trainer.user = user
            trainer.save()

        # Save certificates
        for url in certificate_urls:
            if url:
                cert = TrainerCertificate.objects.create(image_url=url)
                trainer.certificates.add(cert)

        return trainer

    # =====================================================
    # UPDATE
    # =====================================================
    def update(self, instance, validated_data):
        certificate_urls = validated_data.pop("certificates", None)

        # Update Trainer fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update certificates
        if certificate_urls is not None:
            instance.certificates.clear()

            if isinstance(certificate_urls, str):
                try:
                    certificate_urls = json.loads(certificate_urls)
                except Exception:
                    certificate_urls = []

            for url in certificate_urls:
                cert = TrainerCertificate.objects.create(image_url=url)
                instance.certificates.add(cert)

        # Sync User fields
        user = instance.user
        if user:
            for field in ["name", "email", "phno"]:
                if field in validated_data:
                    setattr(user, field, validated_data[field])
            user.save()

        return instance

    # =====================================================
    # SERIALIZER METHODS
    # =====================================================
    def get_profile_pic_url(self, obj):
        request = self.context.get("request")
        if obj.profile_pic and request:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

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
            "expecting_salary",
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
        if not reviews or not reviews.exists():
            return 0
        return round(sum(r.rating for r in reviews.all()) / reviews.count(), 1)

    def get_experience(self, obj):
        return obj.experience

    def get_single_price(self, obj):
        return obj.single_price

    def get_couple_price(self, obj):
        return obj.couple_price

    def get_group_price(self, obj):
        return obj.group_price

  

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
    plan_id = serializers.CharField(
        source="training_field.id",
        read_only=True
    )
    single_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    couple_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    group_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Trainer
        fields = [
            "id",
            "name",
            "phno",
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
            "plan_id",
            "single_price",
            "couple_price",
            "group_price",

            
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
    price_difference = serializers.DecimalField(
    max_digits=10,
    decimal_places=2,
    read_only=True
)

    class Meta:
        model = Trainer
        fields = ["id", "name", "profile_pic", "experience", "star_rating", "single_price","couple_price","group_price", "location","price_difference"]

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
    client_id = serializers.CharField(source="client.id")

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
            "client_id"
        ]

    def get_client_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.client.profile_pic:
            return request.build_absolute_uri(obj.client.profile_pic.url)
        return None


from rest_framework import serializers
from trainer.models import TrainerPayment

class TrainerPaymentSerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)

    class Meta:
        model = TrainerPayment
        fields = [
            "id",
            "trainer",
            "trainer_name",
            "year",
            "month",
            "month_name",
            "salary",
            "status",
            "paid_date",
            "remarks",
        ]

    def get_month_name(self, obj):
        return obj.get_month_display()


class TrainerPaymentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerPayment
        fields = ["salary", "status", "paid_date", "remarks"]

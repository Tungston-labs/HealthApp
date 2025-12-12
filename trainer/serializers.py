from rest_framework import serializers
from .models import Trainer, TrainerCertificate,TrainerAvailability,SlotBooking
from rest_framework import serializers
from client.models import Client
from review.models import TrainerReview

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

from django.contrib.auth.hashers import make_password
from django.conf import settings

class TrainerSerializer(serializers.ModelSerializer):
    certificates = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    certificates_read = serializers.SerializerMethodField()
    profile_pic = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Trainer
        fields = '__all__'
        read_only_fields = ['user']

    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    def get_certificates_read(self, obj):
        request = self.context.get("request")
        return [request.build_absolute_uri(c.image_url) for c in obj.certificates.all()]

    def create(self, validated_data):
        certificates = validated_data.pop("certificates", [])
        password = validated_data.pop("password", None)

        # Create trainer
        trainer = Trainer.objects.create(**validated_data)

        # Hash the password (Trainer is not a User model)
        if password:
            trainer.password = make_password(password)
            trainer.save()

        # Create TrainerCertificate objects
        for url in certificates:
            cert = TrainerCertificate.objects.create(image_url=url)
            trainer.certificates.add(cert)

        return trainer




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

    class Meta:
        model = Trainer
        fields = [
            "id",
            "name",
            "profile_pic",
            "experience",
            "location",
            "certificates",
            "total_reviews",
            "average_rating",
            "rating_breakdown",
            "reviews",
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

    # 🔥 FIX: Pass context to nested serializer
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

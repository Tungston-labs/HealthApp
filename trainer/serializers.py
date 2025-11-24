from rest_framework import serializers
from .models import Trainer, TrainerCertificate,TrainerAvailability
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

class TrainerSerializer(serializers.ModelSerializer):
    certificates = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    adar_image = serializers.CharField(required=False)

    certificates_read = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False)
    profile_pic = serializers.SerializerMethodField()

    class Meta:
        model = Trainer
        fields = '__all__'
        read_only_fields = ['user']

    # -------- FULL URL FOR TRAINER PROFILE PIC ----------
    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    # -------- FULL URL FOR CERTIFICATES ----------
    def get_certificates_read(self, obj):
        request = self.context.get("request")
        return [
            request.build_absolute_uri(c.image_url)
            for c in obj.certificates.all()
        ]

    # ---------------- CREATE ----------------
    def create(self, validated_data):
        cert_urls = validated_data.pop('certificates', [])
        trainer = Trainer.objects.create(**validated_data)

        for url in cert_urls:
            cert_obj = TrainerCertificate.objects.create(image_url=url)
            trainer.certificates.add(cert_obj)

        return trainer

    # ---------------- UPDATE ----------------
    def update(self, instance, validated_data):
        cert_urls = validated_data.pop('certificates', [])
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if cert_urls:
            instance.certificates.all().delete()
            for url in cert_urls:
                cert_obj = TrainerCertificate.objects.create(image_url=url)
                instance.certificates.add(cert_obj)

        if instance.user:
            user = instance.user
            user.name = instance.name
            user.email = instance.email
            if password:
                user.set_password(password)
            user.save()

        return instance
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

    # ---- FULL URL FOR PROFILE PIC ----
    def get_profile_pic(self, obj):
        request = self.context.get("request")
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic.url)
        return None

    # ---- Ratings ----
    def get_star_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews.exists():
            return 0
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    # ---- Experience ----
    def get_experience(self, obj):
        return obj.experience if hasattr(obj, "experience") else None

    # ---- Prices from Plan in context ----
    def get_single_price(self, obj):
        return self.context.get("plan").single_price

    def get_couple_price(self, obj):
        return self.context.get("plan").couple_price

    def get_group_price(self, obj):
        return self.context.get("plan").group_price
  

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

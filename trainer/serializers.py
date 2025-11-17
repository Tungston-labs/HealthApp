from rest_framework import serializers
from .models import Trainer, TrainerCertificate

class TrainerCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerCertificate
        fields = ['id', 'image_url']

class TrainerSerializer(serializers.ModelSerializer):
    certificates = serializers.ListField(
        child=serializers.URLField(),
        write_only=True,
        required=False
    )
    certificates_read = TrainerCertificateSerializer(source='certificates', many=True, read_only=True)
    password = serializers.CharField(write_only=True, required=False)  # optional for trainer creation
    profile_pic = serializers.ImageField(required=False)  # profile pic field

    class Meta:
        model = Trainer
        fields = '__all__'
        read_only_fields = ['user', 'certificates_read', 'status']  # status controlled separately

    def create(self, validated_data):
        cert_urls = validated_data.pop('certificates', [])
        trainer = Trainer.objects.create(**validated_data)

        # Temporarily store password for signal if needed
        password = validated_data.get('password')
        if password:
            trainer._password = password

        # Add certificates
        for url in cert_urls:
            cert_obj = TrainerCertificate.objects.create(image_url=url)
            trainer.certificates.add(cert_obj)

        trainer.save()
        return trainer

    def update(self, instance, validated_data):
        cert_urls = validated_data.pop('certificates', [])
        password = validated_data.pop('password', None)

        # Update Trainer fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update certificates
        if cert_urls:
            instance.certificates.all().delete()
            for url in cert_urls:
                cert_obj = TrainerCertificate.objects.create(image_url=url)
                instance.certificates.add(cert_obj)

        # Update linked User model
        user = instance.user
        if user:
            user.name = instance.name
            user.email = instance.email
            if password:
                user.set_password(password)
            user.save()

        return instance

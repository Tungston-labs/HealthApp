from rest_framework import serializers
from .models import Client
from accounts.models import User

class ClientSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    profile_pic = serializers.ImageField(required=False)

    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.get('email')
        phno = validated_data.get('phno')

        # Create Client instance
        client = Client.objects.create(**validated_data)

        # Create associated User
        user = User.objects.create_user(
            email=email,
            phno=phno,
            password=password,
            role='user',
            name=client.name
        )

        # Link user to client
        client.user = user
        client.save()

        return client

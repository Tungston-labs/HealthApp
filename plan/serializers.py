from rest_framework import serializers
from .models import Plan

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class PlanPendingCountSimpleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    plan_name = serializers.CharField()
    pending_count = serializers.IntegerField()
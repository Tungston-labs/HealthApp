from rest_framework import serializers
from .models import Plan

class PlanSerializer(serializers.ModelSerializer):
    approved_trainers_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Plan
        fields = "__all__"



class PlanPendingCountSimpleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    plan_name = serializers.CharField()
    pending_count = serializers.IntegerField()


class PlanMiniSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plan
        fields = ['id','plan_name']    
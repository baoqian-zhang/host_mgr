from rest_framework import serializers

from api_cost.models import ApiCost


class ApiCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiCost
        fields = "__all__"

from rest_framework import viewsets

from api_cost.models import ApiCost
from api_cost.serializers import ApiCostSerializer


class ApiCostViewSet(viewsets.ModelViewSet):
    queryset = ApiCost.objects.all().order_by("-request_at")
    serializer_class = ApiCostSerializer

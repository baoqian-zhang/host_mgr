from rest_framework import viewsets

from host.models import (
    Host,
    HostStatistic,
)
from host.serializers import (
    HostSerializer,
    HostStatisticSerializer,
)


class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.select_related("idc").all().order_by("id")
    serializer_class = HostSerializer


class HostStatisticViewSet(viewsets.ModelViewSet):
    queryset = (
        HostStatistic.objects.select_related("content_type").all().order_by("-stat_date", "id")
    )
    serializer_class = HostStatisticSerializer

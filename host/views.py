from rest_framework import viewsets

from host.models import (
    Host,
    HostStatistic,
    HostPassword
)
from host.serializers import (
    HostSerializer,
    HostStatisticSerializer,
    HostPasswordSerializer
)


class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.select_related("idc").all().order_by("id")
    serializer_class = HostSerializer


class HostPasswordViewSet(viewsets.ModelViewSet):
    queryset = HostPassword.objects.select_related("host").all().order_by("-changed_at", "-id")
    serializer_class = HostPasswordSerializer


class HostStatisticViewSet(viewsets.ModelViewSet):
    queryset = (
        HostStatistic.objects.select_related("content_type").all().order_by("-stat_date", "id")
    )
    serializer_class = HostStatisticSerializer

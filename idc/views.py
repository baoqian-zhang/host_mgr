from rest_framework import viewsets

from idc.models import IDC
from idc.serializers import IDCSerializer


class IDCViewSet(viewsets.ModelViewSet):
    queryset = IDC.objects.select_related("city").all().order_by("id")
    serializer_class = IDCSerializer

from rest_framework import serializers

from host.models import Host
from host.models import HostPassword
from host.models import HostStatistic


class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = "__all__"


class HostPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostPassword
        fields = "__all__"


class HostStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostStatistic
        fields = "__all__"

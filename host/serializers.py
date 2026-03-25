from django.db import transaction
from rest_framework import serializers

from host.models import Host
from host.models import HostPassword
from host.models import HostStatistic
from host_mgr.crypto.adapters import get_host_password_encryptor
from host_mgr.crypto.passwords import generate_root_password


class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Host
        fields = "__all__"

    def create(self, validated_data):
        with transaction.atomic():
            host = Host.objects.create(**validated_data)

            encryptor = get_host_password_encryptor()
            new_plain = generate_root_password()
            HostPassword.objects.create(
                host=host,
                encrypted_password=encryptor.encrypt(new_plain),
                is_current=True,
            )
            return host


class HostPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostPassword
        fields = "__all__"


class HostStatisticSerializer(serializers.ModelSerializer):

    resource_name = serializers.SerializerMethodField()
    statistic_model = serializers.CharField(source="content_type.model", read_only=True)

    class Meta:
        model = HostStatistic
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def get_resource_name(self, obj):
        if obj.content_object is not None:
            return str(obj.content_object)
        return None

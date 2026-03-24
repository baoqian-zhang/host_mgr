from rest_framework import serializers

from idc.models import IDC


class IDCSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDC
        fields = "__all__"

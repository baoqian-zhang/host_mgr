import uuid

from django.db import models

from host_mgr.fields import NullableJSONStringField


def uuid_hex_str():
    return uuid.uuid4().hex


class BaseModel(models.Model):
    id = models.CharField(
        max_length=32,
        primary_key=True,
        default=uuid_hex_str,
        editable=False,
        verbose_name="ID",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    extra = NullableJSONStringField(
        default=dict, blank=True, null=True, verbose_name="扩展字段"
    )

    def get_extra_value(self, key, default=None):
        extra = getattr(self, "extra", None) or {}
        if not isinstance(extra, dict):
            return default
        return extra.get(key, default)

    def set_extra_value(self, key, value):
        extra = getattr(self, "extra", None) or {}
        if not isinstance(extra, dict):
            extra = {}
        extra[key] = value
        self.extra = extra

    class Meta:
        abstract = True

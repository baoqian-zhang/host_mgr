from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

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

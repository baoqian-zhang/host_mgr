from django.db import models

from host_mgr.base_models import TimeStampedModel


class City(TimeStampedModel):
    name = models.CharField(max_length=64, unique=True, verbose_name="城市名称")
    extra = models.JSONField(default=dict, blank=True, verbose_name="扩展字段")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        db_table = "city"
        verbose_name = "城市"
        verbose_name_plural = "城市"
        ordering = ["id"]

    def __str__(self):
        return f"{self.name}"

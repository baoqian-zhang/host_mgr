from django.db import models

from city.models import City
from host_mgr.base_models import TimeStampedModel


class IDC(TimeStampedModel):
    name = models.CharField(max_length=64, unique=True, verbose_name="机房名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="机房编码")
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="idcs",
        verbose_name="所属城市",
        db_constraint=False,
    )
    extra = models.JSONField(default=dict, blank=True, verbose_name="扩展字段")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        db_table = "idc"
        verbose_name = "机房"
        verbose_name_plural = "机房"
        ordering = ["id"]

    def __str__(self):
        return f"{self.name}({self.code})"

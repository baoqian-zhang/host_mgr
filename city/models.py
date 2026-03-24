from django.db import models

from host_mgr.base_models import BaseModel


class City(BaseModel):
    name = models.CharField(max_length=64, unique=True, verbose_name="城市名称")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        db_table = "city"
        verbose_name = "城市"
        verbose_name_plural = "城市"
        ordering = ["id"]

    def __str__(self):
        return f"{self.name}"

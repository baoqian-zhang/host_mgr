from django.db import models

from city.models import City
from idc.models import IDC
from host_mgr.base_models import TimeStampedModel


class Host(TimeStampedModel):
    hostname = models.CharField(max_length=128, unique=True, verbose_name="主机名")
    ip = models.GenericIPAddressField(unique=True, verbose_name="IP地址")
    ssh_port = models.PositiveIntegerField(default=22, verbose_name="SSH端口")
    idc = models.ForeignKey(
        IDC,
        on_delete=models.PROTECT,
        related_name="hosts",
        verbose_name="所属机房",
        db_constraint=False,
    )
    extra = models.JSONField(default=dict, blank=True, verbose_name="扩展字段")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        db_table = "host"
        verbose_name = "主机"
        verbose_name_plural = "主机"
        ordering = ["id"]

    def __str__(self):
        return f"{self.hostname}({self.ip})"


class HostPassword(TimeStampedModel):
    host = models.ForeignKey(
        Host,
        on_delete=models.CASCADE,
        related_name="passwords",
        verbose_name="主机",
        db_constraint=False,
    )
    encrypted_password = models.TextField(verbose_name="加密后的root密码")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="变更时间")
    valid_from = models.DateTimeField(auto_now_add=True, verbose_name="生效时间")
    valid_to = models.DateTimeField(null=True, blank=True, verbose_name="失效时间")
    is_current = models.BooleanField(default=True, verbose_name="是否当前密码")
    extra = models.JSONField(default=dict, blank=True, verbose_name="扩展字段")

    class Meta:
        db_table = "host_password"
        verbose_name = "主机密码"
        verbose_name_plural = "主机密码"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["host", "is_current"]),
            models.Index(fields=["changed_at"]),
        ]

    def __str__(self):
        return f"{self.host.hostname}-{'current' if self.is_current else 'history'}"


class HostStatistic(TimeStampedModel):
    stat_date = models.DateField(verbose_name="统计日期")
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="host_statistics",
        verbose_name="城市",
        db_constraint=False,
    )
    idc = models.ForeignKey(
        IDC,
        on_delete=models.PROTECT,
        related_name="host_statistics",
        verbose_name="机房",
        db_constraint=False,
    )
    host_count = models.PositiveIntegerField(default=0, verbose_name="主机数量")
    extra = models.JSONField(default=dict, blank=True, verbose_name="扩展字段")

    class Meta:
        db_table = "host_statistic"
        verbose_name = "主机统计"
        verbose_name_plural = "主机统计"
        ordering = ["-stat_date", "city_id", "idc_id"]
        unique_together = ("stat_date", "city", "idc")
        indexes = [
            models.Index(fields=["stat_date", "city", "idc"]),
        ]

    def __str__(self):
        return f"{self.stat_date}-{self.city.name}-{self.idc.name}:{self.host_count}"

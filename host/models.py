from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from idc.models import IDC
from host_mgr.base_models import BaseModel


class Host(BaseModel):
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
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    class Meta:
        db_table = "host"
        verbose_name = "主机"
        verbose_name_plural = "主机"
        ordering = ["id"]

    def __str__(self):
        return f"{self.hostname}({self.ip})"


class HostPassword(BaseModel):
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


class HostStatistic(BaseModel):
    stat_date = models.DateTimeField(auto_now=True, verbose_name="统计时间")
    content_type = models.ForeignKey(
        ContentType,
        db_constraint=False,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="统计资源类型",
        help_text="城市或机房",
    )
    object_id = models.CharField(max_length=32, verbose_name="统计对象ID")
    content_object = GenericForeignKey("content_type", "object_id")
    host_count = models.PositiveIntegerField(default=0, verbose_name="主机数量")

    class Meta:
        db_table = "host_statistic"
        verbose_name = "主机统计"
        verbose_name_plural = "主机统计"
        ordering = ["-stat_date", "content_type_id", "object_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["stat_date", "content_type", "object_id"],
                name="uniq_host_statistic_date_scope",
            ),
        ]
        indexes = [
            models.Index(fields=["stat_date", "content_type", "object_id"]),
        ]

    def __str__(self):
        obj = self.content_object
        label = str(obj) if obj is not None else self.object_id
        return f"{self.stat_date}-{label}:{self.host_count}"

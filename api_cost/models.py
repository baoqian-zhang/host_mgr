from django.db import models

from host_mgr.base_models import BaseModel


class ApiCost(BaseModel):
    path = models.CharField(max_length=255, verbose_name="请求路径")
    method = models.CharField(max_length=16, verbose_name="请求方法")
    status_code = models.PositiveIntegerField(verbose_name="响应状态码")
    duration_ms = models.PositiveIntegerField(verbose_name="耗时(毫秒)")
    request_at = models.DateTimeField(auto_now_add=True, verbose_name="请求时间")
    client_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="客户端IP")

    class Meta:
        db_table = "api_cost"
        verbose_name = "API耗时"
        verbose_name_plural = "API耗时"
        ordering = ["-request_at"]
        indexes = [
            models.Index(fields=["path", "method"]),
            models.Index(fields=["request_at"]),
        ]

    def __str__(self):
        return f"{self.method} {self.path} {self.duration_ms}ms"

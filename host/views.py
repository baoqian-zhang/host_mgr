import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from host_mgr.tasks import app, ping_host_task

from host.models import (
    Host,
    HostStatistic,
)
from host.serializers import (
    HostSerializer,
    HostStatisticSerializer,
)
from host.throttles import PingHostThrottle, PingIpThrottle

logger = logging.getLogger(__name__)


class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.select_related("idc").all().order_by("id")
    serializer_class = HostSerializer

    def get_throttles(self):
        # 仅对 ping 入队（POST）限流；GET 轮询不限流
        if self.action == "ping" and self.request.method == "POST":
            return [PingIpThrottle(), PingHostThrottle()]
        return super().get_throttles()

    @action(detail=True, methods=["post", "get"], url_path="ping", url_name="ping")
    def ping(self, request, pk=None):
        """
        探测主机是否 ping 可达

        - POST：入队，返回 task_id
        /api/v1/hosts/{host-id}/ping/

        - GET ：轮询，传 task_id 返回任务状态/结果
        /api/v1/hosts/{host-id}/ping/?task_id={task-id}
        """
        if request.method == "POST":
            return self._ping_post(request)
        return self._ping_get(request)

    def _ping_post(self, request):
        """入队探测任务。"""
        host = self.get_object()
        data = {
            "host_id": host.id,
            "hostname": host.hostname,
            "ip": str(host.ip),
        }

        try:
            async_result = ping_host_task.delay(host.id)
        except Exception:
            logger.exception("enqueue ping task failed host_id=%s", host.id)
            data["status"] = "internal_error"
            return Response(data, status=status.HTTP_200_OK)

        data["task_id"] = async_result.id
        data["status"] = "queued"
        return Response(data, status=status.HTTP_202_ACCEPTED)

    def _ping_get(self, request):
        """轮询探测任务结果。"""
        host = self.get_object()
        base = {
            "host_id": host.id,
            "hostname": host.hostname,
            "ip": str(host.ip),
        }

        task_id = request.query_params.get("task_id")
        if not task_id:
            data = {**base, "reachable": False, "reason": "task_id_required"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        result = app.AsyncResult(task_id)
        state = (result.state or "").upper()

        data = {**base, "task_id": task_id, "reachable": False}
        http_status = status.HTTP_200_OK

        if state in {"PENDING", "RECEIVED", "RETRY"}:
            data["reason"] = "pending"
        elif state == "STARTED":
            data["reason"] = "started"
        elif state == "SUCCESS":
            payload = result.result
            if isinstance(payload, dict) and payload.get("host_id") == host.id:
                data = payload
            else:
                data["reason"] = "internal_error"
        else:
            data["reason"] = "internal_error"

        return Response(data, status=http_status)


class HostStatisticViewSet(viewsets.ModelViewSet):
    queryset = (
        HostStatistic.objects.select_related("content_type").all().order_by("-stat_date", "id")
    )
    serializer_class = HostStatisticSerializer

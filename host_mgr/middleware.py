import ipaddress
import logging
import time

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from host_mgr.tasks import record_api_cost
from host_mgr.settings import REST_API_PRE_URL

logger = logging.getLogger(__name__)


def _client_ip(request):
    """ 获取真实IP """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        ip = xff.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR") or ""
    if not ip:
        return None
    try:
        ipaddress.ip_address(ip.split("%")[0])
        return ip[:45]
    except ValueError:
        return None


def _enqueue_cost(request, response):
    start = getattr(request, "_api_cost_start", None)
    if start is None or not request.path.startswith(f'/{REST_API_PRE_URL}'):
        return
    duration_ms = int(round((time.perf_counter() - start) * 1000))
    finished_at = timezone.now()
    status_code = getattr(response, "status_code", 0) or 0
    try:
        record_api_cost.delay(
            path=request.path,
            method=request.method,
            status_code=status_code,
            duration_ms=duration_ms,
            client_ip=_client_ip(request),
            request_at_iso=finished_at.isoformat(),
        )
    except Exception:
        logger.exception("enqueue record_api_cost failed path=%s", request.path)


class ApiCostMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request._api_cost_start = time.perf_counter()

    def process_response(self, request, response):
        _enqueue_cost(request, response)
        return response

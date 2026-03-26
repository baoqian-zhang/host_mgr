from rest_framework.throttling import SimpleRateThrottle

from host_mgr.utils import client_ip


class PingIpThrottle(SimpleRateThrottle):
    """按客户端 IP 限流"""

    scope = "ping_ip"

    def get_cache_key(self, request, view):
        ident = client_ip(request) or "unknown"
        return self.cache_format % {"scope": self.scope, "ident": ident[:200]}


class PingHostThrottle(SimpleRateThrottle):
    """按 host 限流"""

    scope = "ping_host"

    def get_cache_key(self, request, view):
        pk = view.kwargs.get("pk")
        if pk is None:
            return None
        return self.cache_format % {"scope": self.scope, "ident": str(pk)}

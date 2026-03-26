from django.test import RequestFactory

from host_mgr.utils import client_ip


def test_client_ip_uses_remote_addr_when_no_xff():
    """未携带 X-Forwarded-For 时，客户端 IP 应取自 META 中的 REMOTE_ADDR。"""
    rf = RequestFactory()
    request = rf.get("/")
    request.META["REMOTE_ADDR"] = "192.168.1.10"
    assert client_ip(request) == "192.168.1.10"


def test_client_ip_prefers_first_xff_hop():
    """存在 X-Forwarded-For（多段逗号分隔）时，应取逗号后第一段作为客户端 IP，忽略 REMOTE_ADDR。"""
    rf = RequestFactory()
    request = rf.get("/")
    request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.1, 10.0.0.2"
    request.META["REMOTE_ADDR"] = "127.0.0.1"
    assert client_ip(request) == "203.0.113.1"


def test_client_ip_returns_none_when_missing_and_invalid():
    """无可用 IP（去掉 REMOTE_ADDR 模拟）或 REMOTE_ADDR 不是合法 IP 时，应返回 None。"""
    rf = RequestFactory()
    req_empty = rf.get("/")
    # RequestFactory 可能默认带 REMOTE_ADDR；去掉以模拟「无任何客户端地址」。
    req_empty.META.pop("REMOTE_ADDR", None)
    assert client_ip(req_empty) is None

    req_bad = rf.get("/")
    req_bad.META["REMOTE_ADDR"] = "not-an-ip"
    assert client_ip(req_bad) is None

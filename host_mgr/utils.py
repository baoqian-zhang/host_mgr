import ipaddress


def client_ip(request):
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

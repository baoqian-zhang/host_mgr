import logging
import os

from celery import Celery
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'host_mgr.settings')
logger = logging.getLogger(__name__)
celery_app = Celery('host_mgr')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()


@celery_app.task
def record_api_cost(path, method, status_code, duration_ms, client_ip, request_at_iso):
    try:
        dt = parse_datetime(request_at_iso) if request_at_iso else None
        kwargs = {
            "path": path[:255],
            "method": (method or "GET"),
            "status_code": status_code,
            "duration_ms": max(0, duration_ms),
            "client_ip": client_ip or None,
            "request_at": dt if dt is not None else timezone.now(),
        }
        from api_cost.serializers import ApiCostSerializer

        serializer = ApiCostSerializer(data=kwargs)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    except Exception:
        logger.exception("record_api_cost failed path=%s method=%s", path, method)

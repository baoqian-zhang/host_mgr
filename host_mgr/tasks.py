import logging
import os

from celery import Celery
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'host_mgr.settings')
logger = logging.getLogger(__name__)
app = Celery('host_mgr')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task
def record_api_cost(path, method, status_code, duration_ms, client_ip, request_at_iso):
    """ 统计api耗时任务 """
    try:
        dt = parse_datetime(request_at_iso) if request_at_iso else None
        from api_cost.models import ApiCost

        ApiCost.objects.create(
            path=path[:255],
            method=(method or "GET"),
            status_code=status_code,
            duration_ms=max(0, duration_ms),
            client_ip=client_ip or None,
            request_at=dt if dt is not None else timezone.now(),
        )
    except Exception:
        logger.exception("record_api_cost failed path=%s method=%s", path, method)


def _calc_city_host_count():
    from django.contrib.contenttypes.models import ContentType

    from city.models import City
    from host.models import Host, HostStatistic

    city_ct = ContentType.objects.get_for_model(City)
    try:
        city_ids = list(
            City.objects.filter(is_active=True).values_list("id", flat=True)
        )

        city_count_map = {
            str(row["city_id"]): row["host_count"]
            for row in Host.objects.filter(is_active=True)
            .values("idc__city_id")
            .annotate(host_count=Count("id"))
            if row["city_id"] is not None
        }
    except Exception:
        logger.exception('query city failed')
        raise

    return [
        HostStatistic(
            content_type_id=city_ct.id,
            object_id=str(city_id),
            host_count=city_count_map.get(str(city_id), 0),
        )
        for city_id in city_ids
    ]


def _calc_idc_host_count():
    from django.contrib.contenttypes.models import ContentType

    from host.models import Host, HostStatistic
    from idc.models import IDC
    idc_ct = ContentType.objects.get_for_model(IDC)

    try:
        idc_ids = list(
            IDC.objects.filter(is_active=True).values_list("id", flat=True)
        )

        idc_count_map = {
            str(row["idc_id"]): row["host_count"]
            for row in Host.objects.filter(is_active=True)
            .values("idc_id")
            .annotate(host_count=Count("id"))
            if row["idc_id"] is not None
        }

    except Exception:
        logger.exception('query idc failed')
        raise

    return [
        HostStatistic(
            content_type_id=idc_ct.id,
            object_id=str(idc_id),
            host_count=idc_count_map.get(str(idc_id), 0),
        )
        for idc_id in idc_ids
    ]


@app.task
def compute_daily_host_statistics():
    """按城市、按机房分别统计活跃主机数量并写入 HostStatistic。"""
    from host.models import HostStatistic

    data = [*_calc_idc_host_count(), *_calc_city_host_count()]
    if not data:
        logger.info('idc and city is empty.')
        return

    batch_size = 500
    try:
        HostStatistic.objects.bulk_create(
            data, batch_size=batch_size, ignore_conflicts=True
        )
    except Exception:
        logger.exception("create host statistic failed")
        raise

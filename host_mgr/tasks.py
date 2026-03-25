import logging
import os
import asyncio
from datetime import timedelta

from celery import Celery
from django.db.models import Count
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from dotenv import load_dotenv

from host_mgr.crypto.adapters import get_host_password_encryptor
from host_mgr.crypto.passwords import generate_root_password
from host.host_operator import HostOperatorAdapter

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'host_mgr.settings')
logger = logging.getLogger(__name__)
app = Celery('host_mgr')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

DB_INSERT_BATCH_SIZE = 500
ROTATE_WINDOW_HOURS = 8
ROTATE_ROOT_PASSWORD_IO_CONCURRENCY = 20
ROTATE_ROOT_PASSWORD_IO_BATCH_SIZE = 200


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

    try:
        HostStatistic.objects.bulk_create(
            data,
            batch_size=DB_INSERT_BATCH_SIZE,
            ignore_conflicts=True,
        )
    except Exception:
        logger.exception("create host statistic failed")
        raise


def _get_eligible_hosts_for_root_rotation(
        now, rotate_window_hours=ROTATE_WINDOW_HOURS):
    """ 获取需要轮换的主机 QuerySet """
    from host.models import Host, HostPassword

    eligible_host_ids = (
        HostPassword.objects.filter(
            is_current=True,
            valid_from__lte=now-timedelta(hours=rotate_window_hours),
        )
        .values_list("host_id", flat=True)
        .distinct()
    )

    return Host.objects.filter(
        is_active=True, id__in=eligible_host_ids
    ).only("id", "hostname", "ip")


def _bulk_rotate_root_passwords(host_id_to_encrypted_password, now):
    """ 批量失效旧 current，并批量写入成功主机的新 current 密码记录 """
    from host.models import HostPassword

    if not host_id_to_encrypted_password:
        return

    host_ids = list(host_id_to_encrypted_password.keys())

    with transaction.atomic():
        # 1. 将修改密码成功的host生效的密码改成失效，记录失效时间
        # 2. 创建新的生效密码并关联host
        HostPassword.objects.filter(
            host_id__in=host_ids, is_current=True
        ).update(is_current=False, valid_to=now)

        new_password_rows = [
            HostPassword(
                host_id=host_id,
                encrypted_password=host_id_to_encrypted_password[host_id],
                valid_from=now,
                is_current=True,
            )
            for host_id in host_ids
        ]
        HostPassword.objects.bulk_create(
            new_password_rows, batch_size=DB_INSERT_BATCH_SIZE
        )


async def _rotate_one_host_root_password_async(host, operator, encryptor, semaphore):
    """
    单机轮换：ping -> change root password -> 生成并返回加密后的密码。
    """

    host_id = str(host.id)
    try:
        async with semaphore:
            ping_ok = await operator.ping_async(host)
            if not ping_ok:
                raise RuntimeError("ping_failed")

            new_plain = generate_root_password()
            change_ok = await operator.change_root_password_async(
                host, new_plain
            )
            if not change_ok:
                raise RuntimeError("change_root_failed")

            encrypted_password = encryptor.encrypt(new_plain)

        logger.info("rotate_host_root_passwords success host_id=%s", host_id)
        return host_id, encrypted_password
    except Exception as e:
        logger.error(
            "rotate_host_root_passwords failed host_id=%s reason=%s",
            host_id,
            str(e),
        )
        return None


async def _rotate_hosts_root_passwords_async(hosts, operator, encryptor):
    """ 异步执行修改传入host密码 """

    semaphore = asyncio.Semaphore(ROTATE_ROOT_PASSWORD_IO_CONCURRENCY)
    succeeded = {}
    buffer = []

    async def _run(buf):
        results = await asyncio.gather(
            *[
                _rotate_one_host_root_password_async(
                    h, operator, encryptor, semaphore
                )
                for h in buf
            ]
        )
        for item in results:
            if item is not None:
                host_id, encrypted_password = item
                succeeded[host_id] = encrypted_password

    # 控制并发量, 以免资源耗尽
    for host in hosts:
        buffer.append(host)
        if len(buffer) >= ROTATE_ROOT_PASSWORD_IO_BATCH_SIZE:
            await _run(buffer)
            buffer = []

    if buffer:
        await _run(buffer)

    return succeeded


@app.task
def rotate_host_root_passwords():
    """ 为所有启用主机生成新 root 密码并加密记录 """
    now = timezone.now()
    encryptor = get_host_password_encryptor()
    operator = HostOperatorAdapter()

    eligible_hosts_qs = _get_eligible_hosts_for_root_rotation(
        now, rotate_window_hours=ROTATE_WINDOW_HOURS
    )

    # 未来若要支持更大规模，可改为“同步分批取数 + async 分批处理”的流式方案，避免一次性占用内存。
    eligible_hosts = list(eligible_hosts_qs)

    succeeded = asyncio.run(
        _rotate_hosts_root_passwords_async(eligible_hosts, operator, encryptor)
    )

    _bulk_rotate_root_passwords(succeeded, now)

    logger.info(
        "rotate_host_root_passwords done succeeded=%s",
        len(succeeded),
    )

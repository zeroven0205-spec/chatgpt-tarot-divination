import logging

from collections import defaultdict
from fastapi import Request

from .cache import CacheClientFactory

_logger = logging.getLogger(__name__)
request_limit_map = defaultdict(list)


def get_real_ipaddr(request: Request) -> str:
    # 优先从 X-Forwarded-For 获取（经过代理的真实 IP）
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # 取第一个 IP（最原始的客户端 IP）
        ip = xff.split(",")[0].strip()
        return ip if ip else "127.0.0.1"
    xrip = request.headers.get("x-real-ip")
    if xrip:
        return xrip
    if not request.client or not request.client.host:
        return "127.0.0.1"
    return request.client.host


def check_rate_limit(key: str, time_window_seconds: int, max_requests: int) -> None:
    cache_client = CacheClientFactory.get_client()
    cache_client.check_rate_limit(key, time_window_seconds, max_requests)

from typing import Final
import random
import os
import fakeredis
import redis

CACHE_TTL_SECONDS: Final = 60  # 缓存默认存活 60 秒

# 表示"这个 key 确实不存在"，用来和 get() 返回 None（"没缓存"）区分开。
# 穿透防护靠它：查库没查到，也把这个哨兵写进缓存，下次就不用再查库。
NULL_SENTINEL: Final = "__NULL__"

# 环境变量：redis://redis:6379/0；本地无容器时为 None
REDIS_URL: Final[str | None] = os.getenv("REDIS_URL")

# 有 REDIS_URL 就用真 Redis，否则 fallback 到 fakeredis（本地无容器也能跑）。
# 注意参数名是 decode_responses（复数，带 s）。
_client = (
    redis.Redis.from_url(REDIS_URL, decode_responses=True)
    if REDIS_URL
    else fakeredis.FakeRedis(decode_responses=True)
)


def get(key: str) -> str | None:
    """
    读缓存。
    - 返回 None          -> 缓存里没有这个 key（未缓存）
    - 返回 NULL_SENTINEL -> 缓存过，但数据库里确实不存在（穿透哨兵）
    - 返回其他字符串     -> 正常缓存值
    """
    value = _client.get(key)
    return value if isinstance(value, str) else None


def set(key: str, value: str, ttl: int = CACHE_TTL_SECONDS) -> None:
    # 抖动：把「同时设置、同时过期」的 key 打散，防止集体过期造成雪崩。
    jitter = random.randint(0, max(1, ttl // 10))
    _client.set(key, value, ex=ttl + jitter)


def delete(key: str) -> None:
    _client.delete(key)


def clear() -> None:
    """
    清空当前 Redis 库。
    用 flushdb 而非 flushall：flushall 会清掉 0-15 所有库，
    多业务共用 Redis 时会误删别人数据。
    """
    _client.flushdb()
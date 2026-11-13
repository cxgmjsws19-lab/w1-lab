from typing import Final
import random
import fakeredis

CACHE_TTL_SECONDS: Final = 60  # 缓存默认存活60秒

# 表示"这个 key 确实不存在"，用来和 get() 返回 None（"没缓存"）区分开。
# 穿透防护靠它：查库没查到，也把这个哨兵写进缓存，下次就不用再查库。
NULL_SENTINEL: Final = "__NULL__"

# W3 换真 Redis 时，只改这一行：
#   import redis
#   _client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

_client: Final = fakeredis.FakeRedis(decode_responses=True)  # Final语义是绑定后不许重新赋值，但不强制


def get(key: str) -> str | None:
    value = _client.get(key)
    return value if isinstance(value, str) else None


def set(key: str, value: str, ttl: int = CACHE_TTL_SECONDS) -> None:
    # 抖动：把「同时设置、同时过期」的 key 打散，防止集体过期造成雪崩。
    jitter = random.randint(0, max(1, ttl // 10))
    _client.set(key, value, ex=ttl + jitter)


def delete(key: str) -> None:
    _client.delete(key)


def clear() -> None:
    _client.flushall()

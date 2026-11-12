from typing import Final

import fakeredis

CACHE_TTL_SECONDS:Final=60  # 缓存默认存活60秒

# W3 换真 Redis 时，只改这一行：
#   import redis
#   _client = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

_client:Final=fakeredis.FakeRedis(decode_responses=True) # Final语义是绑定后不许重新赋值，但不强制

def get(key:str)->str | None:
    value=_client.get(key)
    return value if isinstance(value,str) else None

def set(key:str,value:str,ttl:int=CACHE_TTL_SECONDS)->None:
    _client.set(key,value,ex=ttl)

def delete(key:str)-> None:
    _client.delete(key)

def clear() -> None:
    _client.flushall()
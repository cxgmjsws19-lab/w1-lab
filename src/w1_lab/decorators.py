"""W1 遗留：装饰器（当前未接入 HTTP 服务）。

【三个装饰器各自的现状】

- `timer` / `timer_async` —— **已被 uvicorn 的 access log 覆盖**。
  uvicorn 每条请求都会打 `INFO: 172.18.0.5 - "GET /x HTTP/1.1" 200 OK`，
  要耗时的话加 `--access-log` 参数或用 APM。这两个装饰器只用于练习。

- `retry` —— **有真实价值，但位置不对**。
  它现在捕获 `OSError`，适合网络抖动/连接失败的重试。当前服务没有接它，
  原因是：请求级的写操作重试不安全（可能重复写入），
  而读操作失败了应该让调用方看到错误，而不是偷偷重试。
  **如果项目 1 要调外部 LLM API，这个装饰器可以直接复用**（那里重试是正确的）。

【去留】保留。项目 1 会把 `retry` 真正用上。
"""

import functools
import logging
import time
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

def timer(fn:Callable[P,R]) -> Callable[P,R]:

    @functools.wraps(fn)
    def wrapper(*args:P.args,**kwargs:P.kwargs) -> R:
        start = time.perf_counter()
        try:
            return fn(*args,**kwargs)
        finally:
            cost_ms = (time.perf_counter() - start) * 1000
            logger.debug("%s 耗时%.3fms",fn.__name__,cost_ms)

    return wrapper

def retry(
        times:int=3,
        base_delay:float=0.2,
) -> Callable[[Callable[P,R]],Callable[P,R]]:

    def deco(fn:Callable[P,R]) -> Callable[P,R]:
        @functools.wraps(fn)
        def wrapper(*args:P.args,**kwargs:P.kwargs) -> R:
            last_exc:OSError | None=None
            for attempt in range(1,times+1):
                try:
                    return fn(*args,**kwargs)
                except OSError as exc:
                    last_exc=exc
                    delay=base_delay * (2**(attempt-1))
                    if attempt==times:
                        break
                    logger.warning(
                        "%s 第 %d 次失败：%s，%.1fs 后重试",
                        fn.__name__, attempt, exc, delay,
                    )
                    time.sleep(delay)
            assert last_exc is not None
            logger.error("%s 重试 %d 次后仍失败", fn.__name__, times)
            raise last_exc

        return wrapper

    return deco

def timer_async(
        fn:Callable[P,Awaitable[R]],
)->Callable[P,Coroutine[Any,Any,R]]:

    @functools.wraps(fn)
    async def wrapper(*args:P.args,**kwargs:P.kwargs)->R:
        start = time.perf_counter()
        try:
            return await fn(*args,**kwargs)
        finally:
            cost_ms =(time.perf_counter()-start) * 1000
            logger.debug("%s 耗时 %.3f ms", fn.__name__, cost_ms)

    return wrapper
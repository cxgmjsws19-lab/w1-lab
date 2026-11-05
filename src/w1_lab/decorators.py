import functools
import logging
import time
from collections.abc import Callable
from typing import ParamSpec,TypeVar

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
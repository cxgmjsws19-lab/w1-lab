import asyncio
import logging

import pytest

from w1_lab.decorators import retry,timer_async

def test_retry_stops_after_times()->None:
    calls={"n":0}

    @retry(times=2,base_delay=0.01)
    def always_fail()->None:
        calls["n"] +=1
        raise OSError("boom")

    with pytest.raises(OSError):
        always_fail()

    assert calls["n"]==2

def test_retry_succeeds_on_third_try()->None:
    calls={"n":0}

    @retry(times=3,base_delay=0.01)
    def fail_twice()->str:
        calls["n"]+=1
        if calls["n"] <3:
            raise OSError("boom")
        return "ok"

    assert fail_twice()=="ok"
    assert calls["n"] ==3

def test_timer_async_logs_duration(caplog:pytest.LogCaptureFixture)->None:
    @timer_async
    async def slow()->str:
        await asyncio.sleep(0.02)
        return "ok"

    with caplog.at_level(logging.DEBUG):
        assert asyncio.run(slow())=="ok"

    assert any("耗时" in record.getMessage() for record in caplog.records)
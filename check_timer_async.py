import asyncio
import logging

from w1_lab.decorators import timer_async

logging.basicConfig(level=logging.DEBUG,format="%(levelname)-7s | %(message)s")

@timer_async
async def slow_task()->str:
    await asyncio.sleep(0.5)
    return "done"

async def main() -> None:
    result=await slow_task()
    print("结果:", result)


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import time

async def fake_io(name:str,seconds:float)->str:
    await asyncio.sleep(seconds)
    return name

async def serial()->None:
    start=time.perf_counter()
    for i in range(3):
        await fake_io(f"task{i}",1.0)
    print(f"串行:{time.perf_counter() - start:.2f}s")

async def concurrent()->None:
    start=time.perf_counter()
    await asyncio.gather(*(fake_io(f"task{i}",1.0) for i in range(3)))
    print(f"并发:{time.perf_counter() - start:.2f}s")

async def main()->None:
    await serial()
    await concurrent()

if __name__ == "__main__":
    asyncio.run(main())
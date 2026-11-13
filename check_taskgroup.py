import asyncio
import time

async def work(name:str,delay:float,fail:bool=False)->str:   # 定义一个异步函数（协程） fail:bool=False是否故意抛异常
    await asyncio.sleep(delay)  # 非阻塞地睡眠delay秒
    if fail:
        raise RuntimeError(f"{name}失败")
    print(f"{name}完成")
    return name

async def with_gather()->None:  # 定义协程，演示asyncio.gather的用法
    print("[gather]开始")
    start =time.perf_counter()
    results=await asyncio.gather(   # 同时并发运行三个协程
        work("A",0.1),         #0.1秒后成功
        work("B",0.2,fail=True),   # 0.2秒后抛异常
        work("C",0.3),         # 0.3秒后成功
        return_exceptions=True,    # 把异常当作结果返回
    )
    elapsed=time.perf_counter()-start   # 耗时
    print(f"[gather]结果:{results}")
    print(f"[gather]耗时{elapsed:.2f}s")

async def with_taskgroup()->None:   # 定义协程，演示Python的taskgroup
    print("[taskgroup]开始")
    start=time.perf_counter()
    try:
        async with asyncio.TaskGroup() as tg:   # 创建一个任务组，与gather的区别，如果有任务失败，taskgroup会取消其余任务
            tg.create_task(work("A",0.1))        # 把协程立刻注册为任务并开始并发执行
            tg.create_task(work("B",0.2,fail=True))
            tg.create_task(work("C",0.3))
    except* RuntimeError as eg:
        print(f"[taskgroup] 捕获 {len(eg.exceptions)} 个异常: {eg.exceptions}")
    elapsed=time.perf_counter()-start
    print(f"[taskgroup] 耗时 {elapsed:.2f}s")

async def main()->None:   # 主协程
    await with_gather()
    print()
    await with_taskgroup()

if __name__=="__main__":
    asyncio.run(main())

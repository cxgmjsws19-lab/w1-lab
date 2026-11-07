import asyncio
import time

import httpx


URLS = [
    "https://www.baidu.com",
    "https://www.qq.com",
    "https://mirrors.tuna.tsinghua.edu.cn/",
    "https://www.163.com",
    "https://www.oschina.net",
    "https://www.csdn.net",
]

async def fetch_one(client:httpx.AsyncClient,url:str,sem:asyncio.Semaphore)->int:
    async with sem:
        response = await client.get(url)
        return len(response.text)

async def fetch_with_limit(limit:int)->float:
    sem=asyncio.Semaphore(limit)
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=8,follow_redirects=True) as client:
        await asyncio.gather(*(fetch_one(client,url,sem) for url in URLS))
    return time.perf_counter() - start

async def main() ->None:
    for limit in (1,2,3,6):
        elapsed=await fetch_with_limit(limit)
        print(f"并发度 {limit}：{elapsed:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
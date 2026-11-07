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

def sync_fetch_all() -> int:
    with httpx.Client(timeout=8,follow_redirects=True) as client:
        return sum(len(client.get(url).text) for url in URLS)

async def fetch_one(client:httpx.AsyncClient,url:str)->int:
    response = await client.get(url)
    return len(response.text)

async def async_fetch_all() ->int:
    async with httpx.AsyncClient(timeout=8,follow_redirects=True) as client:
        results = await asyncio.gather(*(fetch_one(client,url) for url in URLS))
    return sum(results)

def main()->None:
    t0=time.perf_counter()
    n1=sync_fetch_all()
    t1=time.perf_counter()
    n2=asyncio.run(async_fetch_all())
    t2=time.perf_counter()

    serial,concurrent=t1-t0,t2-t1
    print(f"串行：{serial:.2f}s，共 {n1} 字符")
    print(f"并发：{concurrent:.2f}s，共 {n2} 字符")
    print(f"提速 {serial / concurrent:.1f} 倍")


if __name__ == "__main__":
    main()

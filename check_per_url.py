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


async def timed(client:httpx.AsyncClient,url:str) -> tuple[str,float,str]:
    start = time.perf_counter()
    try:
        response=await client.get(url)
        return url,time.perf_counter()-start,f"{len(response.text)}字符"
    except Exception as exc:
        return url,time.perf_counter() -start,f"失败:{exc}"

async def main()->None:
    async with httpx.AsyncClient(timeout=8,follow_redirects=True) as client:
        results=await asyncio.gather(*(timed(client,url) for url in URLS))
    for url,cost,info in sorted(results,key=lambda item:-item[1]):
        print(f"{cost:5.2f}s  {url:<45} {info}")


if __name__ == "__main__":
    asyncio.run(main())
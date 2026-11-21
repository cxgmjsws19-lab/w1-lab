"""W1 遗留：按行读日志文件（当前未接入 HTTP 服务）。

【定位】W1 写 CLI 工具时用的：逐行读日志文件，跳过空行。
【为什么 HTTP 服务不用它】当前服务的唯一入口是 `POST /entries`（一次一行，走网络）。
        「从文件批量导入」是一个**真实需要但还没做**的功能。
【去留】保留。项目 1 如果要做批量导入（或离线评测），这个生成器可以直接用——
        它是惰性的（`yield`），大文件也不会一次读进内存。
"""

from collections.abc import Iterator
from pathlib import Path


def iter_lines(path: Path) -> Iterator[str]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                yield stripped
                

import tracemalloc
from pathlib import Path

from w1_lab.reader import iter_lines

path = Path("data/big.log")

tracemalloc.start()
lines=path.read_text(encoding="utf-8").splitlines()
n1=len(lines)
_,peak1=tracemalloc.get_traced_memory()
tracemalloc.stop()

tracemalloc.start()
n2=sum(1 for _ in iter_lines(path))
_,peak2=tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"一次性读入：{n1} 行，峰值 {peak1 / 1024 / 1024:.1f} MB")
print(f"生成器逐行：{n2} 行，峰值 {peak2 / 1024 / 1024:.2f} MB")
print(f"内存差了约 {peak1 / max(peak2, 1):.0f} 倍")

from collections.abc import Iterator
from pathlib import Path

def iter_lines(path:Path)->Iterator[str]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            stripped=line.strip()
            if stripped:
                yield stripped
                

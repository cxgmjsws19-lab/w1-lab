from collections import Counter
from pathlib import Path

from w1_lab.parser import parse_line

def main() -> None:
    lines = Path("data/sample.log").read_text(encoding="utf-8").splitlines()
    entries = [e for e in(parse_line(line) for line in lines) if e is not None]

    print(f"读到{len(lines)}行，解析成功{len(entries)}条")
    for status,count in sorted(Counter(e.status for e in entries).items()):
        print(f"  状态码{status}:{count}次")

if __name__ == "__main__":
    main()

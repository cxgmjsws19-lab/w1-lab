from datetime import datetime
from w1_lab.models import LogEntry

def main() -> None:
    entry = LogEntry(
        ip="10.0.0.1",
        ts=datetime(2026,11,3,9,0,0),
        method="GET",
        path="/api/users",
        status=200,
        size=1234,
        latency=45.2
    )
    print(entry)
    print("状态码:",entry.status)
    print("路径：",entry.path)

if __name__ == "__main__":
    main()
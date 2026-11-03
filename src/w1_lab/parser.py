from datetime import datetime

from .models import LogEntry


def parse_line(line: str) -> LogEntry | None:
    parts = line.strip().split()
    if len(parts) != 7:
        return None

    ts_raw, ip, method, path, status_raw, size_raw, latency_raw = parts

    return LogEntry(
        ip=ip,
        ts=datetime.fromisoformat(ts_raw),
        method=method,
        path=path,
        status=int(status_raw),
        size=int(size_raw),
        latency=float(latency_raw),
    )
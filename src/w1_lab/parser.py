from datetime import datetime

from .models import LogEntry

FIELD_COUNT = 7


class LogFormatError(ValueError):
    """日志行格式不合法。"""


def parse_line(line: str) -> LogEntry:
    parts = line.strip().split()
    if len(parts) != FIELD_COUNT:
        raise LogFormatError(f"期望 {FIELD_COUNT} 个字段，实际 {len(parts)} 个")

    ts_raw, ip, method, path, status_raw, size_raw, latency_raw = parts
    try:
        ts = datetime.fromisoformat(ts_raw)  #解析成datetime对象
    except ValueError as exc:
        raise LogFormatError(str(exc)) from exc

    if ts.tzinfo is None:
        raise LogFormatError(
            f"时间必须带时区，例如 2026-11-20T10:00:00+08:00，实际：{ts_raw}"
        )
    try:
        return LogEntry(
            ip=ip,
            ts=datetime.fromisoformat(ts_raw),
            method=method,
            path=path,
            status=int(status_raw),
            size=int(size_raw),
            latency=float(latency_raw),
        )
    except ValueError as exc:
        raise LogFormatError(str(exc)) from exc
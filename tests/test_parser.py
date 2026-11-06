import pytest

from w1_lab.parser import parse_line,LogFormatError
from datetime import datetime

VALID ="2026-11-05T09:00:00 10.0.0.1 GET /api/users 200 1234 45.2"

def test_parse_line_ok()->None:
    entry = parse_line(VALID)

    assert entry.ip=="10.0.0.1"
    assert entry.status==200
    assert entry.size==1234
    assert entry.latency==45.2
    assert entry.ts==datetime(2026,11,5,9,0,0)

@pytest.mark.parametrize(
    ("line", "why"),
    [
        ("2026-11-05T09:00:00 10.0.0.1 GET /api/users", "字段不足 4 个"),
        ("2026-11-05T09:00:00 10.0.0.1 GET /api/users 200 1234", "字段 6 个"),
        ("2026-11-05T09:00:00 10.0.0.1 GET /x abc 1234 45.2", "状态码非数字"),
        ("2026-11-05T09:00:00 10.0.0.1 GET /x 999 1234 45.2", "状态码超范围"),
        ("not-a-time 10.0.0.1 GET /x 200 1234 45.2", "时间格式错"),
    ],
    ids=["字段不足", "字段6个", "非数字", "超范围", "时间错"],
)

def test_parse_line_invalid(line:str,why:str) -> None:
    with pytest.raises(LogFormatError):
        parse_line(line)
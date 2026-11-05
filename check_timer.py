import logging

from w1_lab.decorators import timer
from w1_lab.parser import parse_line

logging.basicConfig(level=logging.DEBUG,format="%(levelname)s | %(message)s")

measured = timer(parse_line)

line = "2026-11-05T09:00:00 10.0.0.1 GET /api/users 200 1234 45.2" 
entry = measured(line)
print("解析结果:",entry.status)
import logging
from collections import Counter
from pathlib import Path

from w1_lab.config import load_config
from w1_lab.models import LogEntry
from w1_lab.parser import LogFormatError,parse_line
from w1_lab.reader import iter_lines

logger = logging.getLogger("w1_lab")

def main() -> None:
    cfg = load_config()

    logging.basicConfig(
        level = cfg.app.log_level,
        format = "%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt = "%H:%M:%S",
    )

    total=0
    
    entries: list[LogEntry] = []
    bad = 0
    for lineno,line in enumerate(iter_lines(Path(cfg.app.log_file)),start=1):
        total+=1
        try:
            entries.append(parse_line(line))
        except LogFormatError as exc:
            bad += 1
            logger.warning("跳过第%d行:%s",lineno,exc)

    logger.info("读到%d行,成功%d条,跳过%d条",total,len(entries),bad)
    for status,count in Counter(e.status for e in entries).most_common(cfg.report.top_n):
        logger.info("  状态码 %d:%d 次", status, count)

if __name__ == "__main__":
    main()

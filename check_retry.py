import logging
from pathlib import Path

from w1_lab.decorators import retry

logging.basicConfig(level=logging.DEBUG,format="%(levelname)-7s | %(message)s")

calls = {"n":0}

@retry(times=3,base_delay=0.2)
def read_config(path:str) ->str:
    calls["n"] +=1
    if calls["n"]<3:
        raise OSError(f"模拟第 {calls['n']} 次读取失败（文件被占用）")
    return Path(path).read_text(encoding="utf-8")

text =read_config("config.toml")
print(f"最终成功，共调用 {calls['n']} 次，读到 {len(text)} 个字符")
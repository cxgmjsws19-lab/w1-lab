import logging
from logging.handlers import RotatingFileHandler #RotatingFileHandler——按文件大小滚动的日志处理器。写满 maxBytes 就把旧文件改名备份，新建空文件继续写。
from pathlib import Path

log_path=Path("data/app.log")
log_path.parent.mkdir(exist_ok=True) #log_path.parent 是 data 目录；mkdir(exist_ok=True) 创建它。


logger=logging.getLogger("w1_lab.demo")#按名字获取一个 Logger。
logger.setLevel(logging.INFO)

formatter=logging.Formatter(
    "%(asctime)s %(levelname)-7s %(name)s | %(message)s"
)

#文件处理器
file_handler=RotatingFileHandler( #创建文件处理器
    log_path,   #写入data/app.log
    maxBytes=1024,#文件超过1024字节就触发滚动，故意设很小，为了200条日志能快速撑爆，演示滚动效果
    backupCount=3,# 最多保留3个备份
    encoding="utf-8",
)
file_handler.setFormatter(formatter) #给文件处理器绑定上面的格式器。

#控制台处理器
console=logging.StreamHandler()#StreamHandler 默认输出到 stderr（标准错误流），日志会显示在终端。
console.setFormatter(formatter)

#注册处理器，把两个处理器都挂到logger上
#一条日志会依次流经每个 handler：同时写文件和打印到终端。
#这就是日志系统的"分发"模型：logger 产生记录 → 所有 handler 各自处理。
logger.addHandler(file_handler)
logger.addHandler(console)

for i in range(200):
    logger.info("第 %d 条日志，用来把文件撑大", i)

print("\n--- 生成的文件 ---")
for p in sorted(Path("data").glob("app.log*")):
    print(f"  {p.name}  {p.stat().st_size} 字节")
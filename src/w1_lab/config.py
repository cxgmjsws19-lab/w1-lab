"""W1 遗留：TOML 配置加载（当前未接入 HTTP 服务）。

【定位】这是 W1 写 CLI 日志分析工具时的配置层：从 `config.toml` 读
        `log_file` / `log_level` / `top_n`，用 pydantic 校验。
【为什么 HTTP 服务不用它】服务侧配置走**环境变量**（`DATABASE_URL` / `REDIS_URL` /
        `DEBUG`），这是 12-factor app 的惯例——容器化部署时环境变量比挂配置文件
        更好管理，也不会把配置打进镜像。
【去留】保留作为学习产物（演示"用 pydantic 校验配置文件，写错当场报错"）。
        如果项目 1 需要 CLI 入口，这里可以直接复用。
"""

import tomllib
from pathlib import Path

from pydantic import BaseModel


class AppConfig(BaseModel):
    log_file: str
    log_level: str


class ReportConfig(BaseModel):
    top_n:int


class Config(BaseModel):
    app:AppConfig
    report:ReportConfig


def load_config(path:Path=Path("config.toml")) -> Config:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    return Config.model_validate(raw)
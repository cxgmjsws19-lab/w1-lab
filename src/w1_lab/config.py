import tomllib
from pathlib import Path

from pydantic import BaseModel

class AppConfig(BaseModel):
    log_file:str
    log_level:str


class ReportConfig(BaseModel):
    top_n:int


class Config(BaseModel):
    app:AppConfig
    report:ReportConfig


def load_config(path:Path=Path("config.toml")) -> Config:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    return Config.model_validate(raw)
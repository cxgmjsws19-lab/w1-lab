from datetime import datetime
from ipaddress import ip_address

from pydantic import BaseModel, Field, field_validator


class LogEntry(BaseModel):
    ip: str
    ts: datetime
    method: str
    path: str
    status: int = Field(ge=100, le=599)
    size: int = Field(ge=0)
    latency: float = Field(ge=0)

    @field_validator("ip")
    @classmethod
    def _check_ip(cls, value: str) -> str:
        """校验 ip 字段必须是合法的 IPv4/IPv6 地址。

        不合法时 ip_address 抛 ValueError，pydantic 会转成 422。
        注意：部分访问日志会用 "-" 占位（客户端 IP 未知），
        如果你接入的日志源有这种情况，应先在 parse_line 里把 "-" 转成 None，
        而不是在这里放宽校验。
        """
        ip_address(value)
        return value


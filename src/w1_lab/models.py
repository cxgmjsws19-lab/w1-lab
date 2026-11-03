from datetime import datetime
from pydantic import BaseModel,Field

class LogEntry(BaseModel):
    ip:str
    ts:datetime
    method:str
    path:str
    status:int = Field(ge=100,le=599)
    size:int = Field(ge=0)
    latency:float = Field(ge=0)
    
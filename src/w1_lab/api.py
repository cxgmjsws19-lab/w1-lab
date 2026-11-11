from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel
from sqlalchemy import func,select
from collections.abc import Iterator
from sqlalchemy.orm import Session

from .db import LogEntryRow,SessionLocal
from .models import LogEntry
from .parser import LogFormatError,parse_line

app=FastAPI(title="w1-lab API")


def get_db()->Iterator[Session]:
    with SessionLocal() as session: # 准备：开连接
        yield session  # 交给接口函数，暂停

class ParseRequest(BaseModel):
    line:str

class HealthResponse(BaseModel):
    status:str

@app.get("/health",response_model=HealthResponse)
def health()->HealthResponse:
    return HealthResponse(status="ok")

@app.post("/entries", response_model=LogEntry,status_code=201)
def create_entry(
    request: ParseRequest,
    session:Session=Depends(get_db),
    ) -> LogEntry:
    try:
        entry = parse_line(request.line)
    except LogFormatError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    session.add(LogEntryRow(**entry.model_dump()))
    session.commit()
    return entry

class StatsResponse(BaseModel):
    total:int
    by_status:dict[int,int]

@app.get("/entries/stats",response_model=StatsResponse)
def entries_stats(session:Session=Depends(get_db))->StatsResponse:
    
    total=session.scalar(select(func.count()).select_from(LogEntryRow)) or 0
    rows=session.execute(
        select(LogEntryRow.status,func.count()).group_by(LogEntryRow.status)
    ).all()

    return StatsResponse(total=total,by_status={s:c for s,c in rows})



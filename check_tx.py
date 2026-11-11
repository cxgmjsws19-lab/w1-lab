from datetime import datetime

from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session

from w1_lab.db import Base,LogEntryRow

engine=create_engine(
    "sqlite:///tx_demo.db",
    connect_args={"check_same_thread":False},
)
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

def make(i:int) ->LogEntryRow:
    return LogEntryRow(
        ip=f"10.0.0.{i}",
        ts =datetime(2026,11,11,12,i),
        method="POST",
        path=f"/x/{i}",
        status=200,
        size=i,
        latency=1.0,
    )

def count()->int:
    with Session(engine) as session:
        return len(session.scalars(select(LogEntryRow)).all())

with Session(engine) as session:
    for i in range(3):
        session.add(make(i))
    session.commit()
print(f"场景1 三条都成功 → 库里 {count()} 条")

with Session(engine) as session:
    try:
        for i in range(3,6):
            session.add(make(i))
            if i==4:
                raise RuntimeError("模拟第 2 条处理时出错")
        session.commit()
    except RuntimeError as exc:
        session.rollback()
        print(f"场景2 出错：{exc}")
print(f"场景2 回滚后 → 库里 {count()} 条（应该还是 3 条）")
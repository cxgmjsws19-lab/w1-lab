from datetime import datetime

from sqlalchemy import create_engine,event,select
from sqlalchemy.orm import Session,selectinload,joinedload


from w1_lab.db import Base,LogEntryRow,UserRow

engine=create_engine(
    "sqlite:///n1_demo.db",
    connect_args={"check_same_thread":False},
)
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

counter={"n":0}

# 装饰器：在 engine 上注册监听器，事件是 before_cursor_execute——每条 SQL 执行前触发。装饰的函数就是回调。
@event.listens_for(engine,"before_cursor_execute")
def _count(conn,cursor,statement,params,context,executemany)->None:
    counter["n"]+=1

def seed()->None:
    with Session(engine) as session:
        users=[UserRow(name=f"user{i}")for i in range(5)]
        session.add_all(users)
        session.flush()
        # 把挂起的 INSERT 发到数据库（但不提交事务）。这样 user.id 这个自增主键就被数据库填上了。后面 5 条日志需要 user_id=user.id，所以必须先 flush 拿到 id。
        for i,user in enumerate(users):
            session.add(
                LogEntryRow(
                    ip=f"10.0.0.{i}",
                    ts=datetime(2026,11,11,10,i),
                    method="GET",
                    path=f"/api/{i}",
                    status=200,
                    size=100+i,
                    latency=1.0+i,
                    user_id=user.id,
                )
            )
        session.commit()

def run(label:str,mode:str)->None:
    counter["n"]=0
    with Session(engine) as session:
        stmt=select(LogEntryRow).order_by(LogEntryRow.id)
        if mode =="selectin":
            stmt=stmt.options(selectinload(LogEntryRow.user))
        elif mode =="joined":
            stmt=stmt.options(joinedload(LogEntryRow.user))
        entries=session.scalars(stmt).all()
        names=[e.user.name if e.user else None for e in entries]

    print(f"{label}: {counter['n']} 条 SQL，names={names}")

seed()
run("懒加载（N+1）", "lazy")
run("selectinload", "selectin")
run("joinedload", "joined")

# 1. 建一个独立的 demo 数据库 n1_demo.db
# 2. 删表重建（干净环境）
# 3. 挂一个"SQL 计数器"：每执行一条 SQL 就 +1
# 4. seed()：插 1 个用户 + 5 条日志（关联到该用户）
# 5. run(懒加载)：查 5 条日志，逐条访问 e.user.name → 统计 SQL 条数
# 6. run(selectinload)：同上，但预加载 user → 统计 SQL 条数
# 7. 对比两者 SQL 条数，直观展示 N+1
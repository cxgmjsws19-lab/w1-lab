from datetime import datetime

from sqlalchemy import DateTime,String,create_engine,ForeignKey
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker,relationship

import os
# DATABASE_URL ="sqlite:///w1lab.db"
# DATABASE_URL="postgresql+psycopg://postgres:devpass@127.0.0.1:5432/w1lab"
#URL 格式：postgresql+psycopg://用户:密码@主机:端口/数据库名
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:devpass@127.0.0.1:5432/w1lab",
)

engine=create_engine(DATABASE_URL)  #创建引擎，引擎是连接池+方言+配置的集合，是数据库操作的入口
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False) #创建会话工厂，会话绑定到engine引擎，commit不让对象过期

class Base(DeclarativeBase):      #定义所有ORM模型的基类，所有模型继承Base，SQLAlchemy通过它收集表定义，建立映射
    pass

class UserRow(Base):    #定义用户模型，继承Base
    __tablename__ ="users" #数据库表名

    password_hash:Mapped[str]=mapped_column(String(256))  #存密码哈希（绝不存明文密码）
    id:Mapped[int] = mapped_column(primary_key=True)     #在 PostgreSQL + SQLAlchemy 下，Integer 主键默认会生成自增序列（SERIAL/IDENTITY），所以插入时不需要手动给 id。
    name:Mapped[str]=mapped_column(String(64))

#ORM 关系（不是数据库列）：UserRow 和 LogEntryRow 的一对多关系。
# ORM 层的一对多关系（不是数据库列）。它让 UserRow 对象能通过 .entries 属性直接访问"这个用户的所有日志"，无需手写 JOIN。
#back_populates="user" 表示：这个关系在对端（LogEntryRow）上对应的属性名叫 user。  
    entries:Mapped[list["LogEntryRow"]]=relationship(back_populates="user")

class LogEntryRow(Base):
    __tablename__="log_entries"

    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int | None]=mapped_column(ForeignKey("users.id"))
    user:Mapped["UserRow | None"]=relationship(back_populates="entries")
    ip:Mapped[str]=mapped_column(String(64),index=True)
    ts:Mapped[datetime]=mapped_column(DateTime)
    method:Mapped[str]=mapped_column(String(16))
    path:Mapped[str]=mapped_column(String(256))
    status:Mapped[int]
    size:Mapped[int]
    latency:Mapped[float]
    user_agent:Mapped[str | None]=mapped_column(String(256))

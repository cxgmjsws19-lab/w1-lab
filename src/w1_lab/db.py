from datetime import datetime

from sqlalchemy import DateTime,String,create_engine
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker

DATABASE_URL ="sqlite:///w1lab.db"

engine=create_engine(DATABASE_URL,connect_args={"check_same_thread":False})
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class LogEntryRow(Base):
    __tablename__="log_entries"

    id:Mapped[int]=mapped_column(primary_key=True)
    ip:Mapped[str]=mapped_column(String(64))
    ts:Mapped[datetime]=mapped_column(DateTime)
    method:Mapped[str]=mapped_column(String(16))
    path:Mapped[str]=mapped_column(String(256))
    status:Mapped[int]
    size:Mapped[int]
    latency:Mapped[float]

from datetime import datetime

from sqlalchemy import DateTime,String,create_engine,ForeignKey
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,sessionmaker,relationship

# DATABASE_URL ="sqlite:///w1lab.db"
DATABASE_URL="postgresql+psycopg://postgres:devpass@127.0.0.1:5432/w1lab"

engine=create_engine(DATABASE_URL)
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class UserRow(Base):
    __tablename__ ="users"

    password_hash:Mapped[str]=mapped_column(String(256))
    id:Mapped[int] = mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(64))

    entries:Mapped[list["LogEntryRow"]]=relationship(back_populates="user")

class LogEntryRow(Base):
    __tablename__="log_entries"

    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int | None]=mapped_column(ForeignKey("users.id"))
    user:Mapped["UserRow | None"]=relationship(back_populates="entries")
    ip:Mapped[str]=mapped_column(String(64))
    ts:Mapped[datetime]=mapped_column(DateTime)
    method:Mapped[str]=mapped_column(String(16))
    path:Mapped[str]=mapped_column(String(256))
    status:Mapped[int]
    size:Mapped[int]
    latency:Mapped[float]
    user_agent:Mapped[str | None]=mapped_column(String(256))

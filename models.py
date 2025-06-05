# models.py
import os
from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite+aiosqlite:///./hihigs.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id     = Column(Integer, primary_key=True)
    username    = Column(String(255), nullable=True)
    role        = Column(String(10), nullable=False)      # "tutor" или "student"
    tutor_code = Column(String(32), nullable=True, unique=True)
    token       = Column(String(255), nullable=True)      # Yandex.Disk API token
    subscribe_to= Column(Integer, ForeignKey("users.user_id"), nullable=True)
    subscribers = relationship("User", backref="tutor", remote_side=[user_id])

class TrackedFolder(Base):
    __tablename__ = "tracked_folders"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    tutor_id    = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    path        = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint("tutor_id", "path", name="uq_tutor_folder"),)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

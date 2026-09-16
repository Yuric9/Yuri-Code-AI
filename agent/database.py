"""Persistence layer for Yuri Code AI: projects, conversations, messages and memories."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


def _database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured
    path = Path(os.getenv("YURI_DATA_DIR", ".yuri-data"))
    path.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(path / 'yuri_code_ai.db').resolve()}"


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    path: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    conversations: Mapped[list["ConversationRecord"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ConversationRecord(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    project: Mapped[Project | None] = relationship(back_populates="conversations")
    messages: Mapped[list["MessageRecord"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class MessageRecord(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    conversation: Mapped[ConversationRecord] = relationship(back_populates="messages")


class MemoryRecord(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(32), index=True, default="project")
    key: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ResearchRecord(Base):
    __tablename__ = "research"

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


engine = create_engine(_database_url(), future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def init_db() -> None:
    """Create missing tables without destroying existing data."""
    Base.metadata.create_all(engine)


def remember(scope: str, key: str, content: str) -> None:
    with SessionLocal.begin() as db:
        record = db.scalar(select(MemoryRecord).where(MemoryRecord.scope == scope, MemoryRecord.key == key))
        if record:
            record.content = content
        else:
            db.add(MemoryRecord(scope=scope, key=key, content=content))


def recall(scope: str, key: str | None = None) -> list[MemoryRecord]:
    with SessionLocal() as db:
        stmt = select(MemoryRecord).where(MemoryRecord.scope == scope)
        if key:
            stmt = stmt.where(MemoryRecord.key == key)
        return list(db.scalars(stmt).all())


def log_research(query: str, source_url: str | None, result: str | None) -> None:
    with SessionLocal.begin() as db:
        db.add(ResearchRecord(query=query, source_url=source_url, result=result))

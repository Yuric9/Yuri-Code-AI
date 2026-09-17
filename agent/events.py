"""Durable task execution events."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base, SessionLocal


class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(index=True)
    phase: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def record(task_id: int, phase: str, message: str) -> None:
    with SessionLocal.begin() as db:
        db.add(TaskEvent(task_id=task_id, phase=phase, message=message))


def list_events(task_id: int, limit: int = 100) -> list[TaskEvent]:
    with SessionLocal() as db:
        stmt = select(TaskEvent).where(TaskEvent.task_id == task_id).order_by(TaskEvent.id.desc()).limit(limit)
        return list(reversed(list(db.scalars(stmt).all())))

"""Persistent task orchestration for Yuri Code AI.

The orchestrator deliberately has no application-level task/search/file quota. It
persists lifecycle state so a web request can enqueue work and a worker can resume it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from threading import Lock
from typing import Callable

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base, SessionLocal, init_db


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRecord(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal: Mapped[str] = mapped_column(Text)
    workspace: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.QUEUED.value, index=True)
    phase: Mapped[str] = mapped_column(String(64), default="queued")
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class TaskSnapshot:
    id: int
    goal: str
    workspace: str
    status: str
    phase: str
    result: str | None
    error: str | None


class TaskOrchestrator:
    """Small durable queue suitable for local V1 and easy to replace by a worker queue later."""

    def __init__(self) -> None:
        init_db()
        self._lock = Lock()

    def enqueue(self, goal: str, workspace: str) -> TaskSnapshot:
        with SessionLocal.begin() as db:
            record = TaskRecord(goal=goal, workspace=workspace)
            db.add(record)
            db.flush()
            return self._snapshot(record)

    def get(self, task_id: int) -> TaskSnapshot | None:
        with SessionLocal() as db:
            record = db.get(TaskRecord, task_id)
            return self._snapshot(record) if record else None

    def claim_next(self) -> TaskSnapshot | None:
        with self._lock, SessionLocal.begin() as db:
            record = db.scalar(select(TaskRecord).where(TaskRecord.status == TaskStatus.QUEUED.value).order_by(TaskRecord.id).limit(1))
            if not record:
                return None
            record.status = TaskStatus.RUNNING.value
            record.phase = "running"
            return self._snapshot(record)

    def update(self, task_id: int, *, phase: str | None = None, status: TaskStatus | None = None, result: str | None = None, error: str | None = None) -> TaskSnapshot | None:
        with SessionLocal.begin() as db:
            record = db.get(TaskRecord, task_id)
            if not record:
                return None
            if phase is not None:
                record.phase = phase
            if status is not None:
                record.status = status.value
            if result is not None:
                record.result = result
            if error is not None:
                record.error = error
            return self._snapshot(record)

    def cancel(self, task_id: int) -> TaskSnapshot | None:
        return self.update(task_id, status=TaskStatus.CANCELLED, phase="cancelled")

    @staticmethod
    def _snapshot(record: TaskRecord) -> TaskSnapshot:
        return TaskSnapshot(record.id, record.goal, record.workspace, record.status, record.phase, record.result, record.error)


def run_task(orchestrator: TaskOrchestrator, task: TaskSnapshot, runner: Callable[[str, str, Callable[[str], None]], str]) -> TaskSnapshot:
    """Run one claimed task and persist every lifecycle boundary."""
    try:
        def progress(phase: str) -> None:
            orchestrator.update(task.id, phase=phase)

        result = runner(task.goal, task.workspace, progress)
        return orchestrator.update(task.id, status=TaskStatus.COMPLETED, phase="completed", result=result)  # type: ignore[return-value]
    except Exception as exc:
        return orchestrator.update(task.id, status=TaskStatus.FAILED, phase="failed", error=str(exc))  # type: ignore[return-value]

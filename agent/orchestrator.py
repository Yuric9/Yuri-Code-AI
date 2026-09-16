"""Durable task orchestration for Yuri Code AI."""
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
    worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    """SQLite/PostgreSQL-backed queue with restart recovery and no application quota."""

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

    def recover_running(self) -> int:
        """Put interrupted work back in the queue after an API/worker restart."""
        with SessionLocal.begin() as db:
            records = list(db.scalars(select(TaskRecord).where(TaskRecord.status == TaskStatus.RUNNING.value)).all())
            for record in records:
                record.status = TaskStatus.QUEUED.value
                record.phase = "recovered"
                record.worker_id = None
            return len(records)

    def _claim_record(self, db, record: TaskRecord, worker_id: str) -> TaskSnapshot:
        record.status = TaskStatus.RUNNING.value
        record.phase = "running"
        record.worker_id = worker_id
        record.started_at = datetime.now(timezone.utc)
        return self._snapshot(record)

    def claim_next(self, worker_id: str) -> TaskSnapshot | None:
        with self._lock, SessionLocal.begin() as db:
            record = db.scalar(select(TaskRecord).where(TaskRecord.status == TaskStatus.QUEUED.value).order_by(TaskRecord.id).limit(1))
            if not record:
                return None
            return self._claim_record(db, record, worker_id)

    def claim(self, task_id: int, worker_id: str) -> TaskSnapshot | None:
        """Atomically claim one specific queued task, used by the embedded API worker."""
        with self._lock, SessionLocal.begin() as db:
            record = db.get(TaskRecord, task_id)
            if not record or record.status != TaskStatus.QUEUED.value:
                return None
            return self._claim_record(db, record, worker_id)

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
        with SessionLocal.begin() as db:
            record = db.get(TaskRecord, task_id)
            if not record:
                return None
            if record.status == TaskStatus.RUNNING.value:
                record.phase = "cancel_requested"
                return self._snapshot(record)
            record.status = TaskStatus.CANCELLED.value
            record.phase = "cancelled"
            return self._snapshot(record)

    @staticmethod
    def _snapshot(record: TaskRecord) -> TaskSnapshot:
        return TaskSnapshot(record.id, record.goal, record.workspace, record.status, record.phase, record.result, record.error)


def run_task(orchestrator: TaskOrchestrator, task: TaskSnapshot, runner: Callable[[str, str, Callable[[str], None]], str]) -> TaskSnapshot:
    """Run a claimed task and persist lifecycle boundaries."""
    try:
        def progress(phase: str) -> None:
            orchestrator.update(task.id, phase=phase)

        result = runner(task.goal, task.workspace, progress)
        return orchestrator.update(task.id, status=TaskStatus.COMPLETED, phase="completed", result=result)  # type: ignore[return-value]
    except Exception as exc:
        return orchestrator.update(task.id, status=TaskStatus.FAILED, phase="failed", error=str(exc))  # type: ignore[return-value]

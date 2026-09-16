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
from .events import record as record_event


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
    """SQLite/PostgreSQL-backed queue with restart recovery and durable lifecycle events."""

    def __init__(self) -> None:
        init_db()
        self._lock = Lock()

    def _event(self, task_id: int, phase: str, message: str) -> None:
        try:
            record_event(task_id, phase, message)
        except Exception:
            # Event logging must never bring down the worker.
            pass

    def enqueue(self, goal: str, workspace: str) -> TaskSnapshot:
        with SessionLocal.begin() as db:
            record = TaskRecord(goal=goal, workspace=workspace)
            db.add(record)
            db.flush()
            snapshot = self._snapshot(record)
        self._event(snapshot.id, "queued", "Task created")
        return snapshot

    def get(self, task_id: int) -> TaskSnapshot | None:
        with SessionLocal() as db:
            record = db.get(TaskRecord, task_id)
            return self._snapshot(record) if record else None

    def recover_running(self) -> int:
        with SessionLocal.begin() as db:
            records = list(db.scalars(select(TaskRecord).where(TaskRecord.status == TaskStatus.RUNNING.value)).all())
            ids = []
            for record in records:
                record.status = TaskStatus.QUEUED.value
                record.phase = "recovered"
                record.worker_id = None
                ids.append(record.id)
        for task_id in ids:
            self._event(task_id, "recovered", "Task returned to queue after worker restart")
        return len(ids)

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
            snapshot = self._claim_record(db, record, worker_id)
        self._event(snapshot.id, "running", f"Claimed by {worker_id}")
        return snapshot

    def claim(self, task_id: int, worker_id: str) -> TaskSnapshot | None:
        with self._lock, SessionLocal.begin() as db:
            record = db.get(TaskRecord, task_id)
            if not record or record.status != TaskStatus.QUEUED.value:
                return None
            snapshot = self._claim_record(db, record, worker_id)
        self._event(snapshot.id, "running", f"Claimed by {worker_id}")
        return snapshot

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
            snapshot = self._snapshot(record)
        if phase is not None:
            self._event(task_id, phase, error or phase)
        if status is not None:
            self._event(task_id, status.value, status.value)
        return snapshot

    def cancel(self, task_id: int) -> TaskSnapshot | None:
        with SessionLocal.begin() as db:
            record = db.get(TaskRecord, task_id)
            if not record:
                return None
            if record.status == TaskStatus.RUNNING.value:
                record.phase = "cancel_requested"
                snapshot = self._snapshot(record)
                requested = True
            else:
                record.status = TaskStatus.CANCELLED.value
                record.phase = "cancelled"
                snapshot = self._snapshot(record)
                requested = False
        self._event(task_id, snapshot.phase, "Cancellation requested" if requested else "Task cancelled")
        return snapshot

    @staticmethod
    def _snapshot(record: TaskRecord) -> TaskSnapshot:
        return TaskSnapshot(record.id, record.goal, record.workspace, record.status, record.phase, record.result, record.error)


def run_task(orchestrator: TaskOrchestrator, task: TaskSnapshot, runner: Callable[[str, str, Callable[[str], None]], str]) -> TaskSnapshot:
    try:
        def progress(phase: str) -> None:
            orchestrator.update(task.id, phase=phase)

        result = runner(task.goal, task.workspace, progress)
        return orchestrator.update(task.id, status=TaskStatus.COMPLETED, phase="completed", result=result)  # type: ignore[return-value]
    except Exception as exc:
        return orchestrator.update(task.id, status=TaskStatus.FAILED, phase="failed", error=str(exc))  # type: ignore[return-value]

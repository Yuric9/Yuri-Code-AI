"""FastAPI service for the durable Yuri Code AI task queue."""
from __future__ import annotations

import os
import socket
from pathlib import Path
from threading import Thread

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.events import list_events
from agent.orchestrator import TaskOrchestrator, TaskSnapshot
from agent.worker import execute
from server.git_api import router as git_router
from server.workspace_api import router as workspace_router

app = FastAPI(title="Yuri Code AI", version="0.6.0")
app.include_router(git_router)
app.include_router(workspace_router)
orchestrator = TaskOrchestrator()


class TaskRequest(BaseModel):
    message: str = Field(min_length=1)
    workspace: str | None = None


class TaskResponse(BaseModel):
    id: int
    goal: str
    workspace: str
    status: str
    phase: str
    result: str | None = None
    error: str | None = None


class TaskEventResponse(BaseModel):
    id: int
    task_id: int
    phase: str
    message: str
    created_at: str


def _response(task: TaskSnapshot) -> TaskResponse:
    return TaskResponse(id=task.id, goal=task.goal, workspace=task.workspace, status=task.status, phase=task.phase, result=task.result, error=task.error)


def _workspace(value: str | None) -> str:
    root = Path(value or os.getenv("YURI_WORKSPACE", "./workspace")).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return str(root)


def _local_worker_id() -> str:
    return f"api-local:{socket.gethostname()}:{os.getpid()}"


def _run_local(task_id: int) -> None:
    task = orchestrator.claim(task_id, _local_worker_id())
    if not task:
        return
    try:
        execute(task, orchestrator)
    except Exception as exc:
        orchestrator.update(task.id, phase="failed", error=str(exc))


@app.on_event("startup")
def recover_queue() -> None:
    orchestrator.recover_running()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "yuri-code-ai", "queue": "durable", "events": "durable"}


@app.post("/tasks", response_model=TaskResponse, status_code=202)
def create_task(payload: TaskRequest) -> TaskResponse:
    task = orchestrator.enqueue(payload.message.strip(), _workspace(payload.workspace))
    if os.getenv("YURI_API_RUN_LOCAL_WORKER", "true").lower() in {"1", "true", "yes"}:
        Thread(target=_run_local, args=(task.id,), daemon=True, name=f"yuri-task-{task.id}").start()
    return _response(task)


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int) -> TaskResponse:
    task = orchestrator.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return _response(task)


@app.get("/tasks/{task_id}/events", response_model=list[TaskEventResponse])
def get_task_events(task_id: int, limit: int = 100) -> list[TaskEventResponse]:
    if not orchestrator.get(task_id):
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    safe_limit = max(1, min(limit, 500))
    return [
        TaskEventResponse(id=e.id, task_id=e.task_id, phase=e.phase, message=e.message, created_at=e.created_at.isoformat())
        for e in list_events(task_id, safe_limit)
    ]


@app.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(task_id: int) -> TaskResponse:
    task = orchestrator.cancel(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return _response(task)

"""FastAPI service for the durable Yuri Code AI task queue."""
from __future__ import annotations

import os
from pathlib import Path
from threading import Thread

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.orchestrator import TaskOrchestrator, TaskSnapshot
from agent.worker import execute

app = FastAPI(title="Yuri Code AI", version="0.4.0")
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


def _response(task: TaskSnapshot) -> TaskResponse:
    return TaskResponse(id=task.id, goal=task.goal, workspace=task.workspace, status=task.status, phase=task.phase, result=task.result, error=task.error)


def _workspace(value: str | None) -> str:
    root = Path(value or os.getenv("YURI_WORKSPACE", "./workspace")).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return str(root)


def _run_local(task_id: int) -> None:
    task = orchestrator.get(task_id)
    if not task:
        return
    try:
        execute(task, orchestrator)
    except Exception as exc:
        orchestrator.update(task.id, phase="failed", error=str(exc))


@app.on_event("startup")
def recover_queue() -> None:
    """Recover interrupted tasks; an external worker can then process them."""
    orchestrator.recover_running()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "yuri-code-ai", "queue": "durable"}


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


@app.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(task_id: int) -> TaskResponse:
    task = orchestrator.cancel(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return _response(task)

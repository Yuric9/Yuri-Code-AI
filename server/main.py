"""FastAPI service that turns Yuri Code AI into a persistent task endpoint."""
from __future__ import annotations

import os
from pathlib import Path
from threading import Thread

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.main import build_agent
from agent.orchestrator import TaskOrchestrator, TaskSnapshot, run_task
from openhands.sdk import Conversation

app = FastAPI(title="Yuri Code AI", version="0.3.0")
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
    return TaskResponse(
        id=task.id,
        goal=task.goal,
        workspace=task.workspace,
        status=task.status,
        phase=task.phase,
        result=task.result,
        error=task.error,
    )


def _workspace(value: str | None) -> str:
    root = Path(value or os.getenv("YURI_WORKSPACE", "./workspace")).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return str(root)


def _run(task_id: int) -> None:
    task = orchestrator.get(task_id)
    if not task:
        return
    agent = build_agent()
    conversation = Conversation(agent=agent, workspace=task.workspace)

    def runner(goal: str, workspace: str, progress):
        progress("planning")
        conversation.send_message(goal)
        progress("executing")
        conversation.run()
        progress("validating")
        return "Tarefa executada pelo agente. Consulte o workspace para os arquivos e alterações produzidos."

    run_task(orchestrator, task, runner)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "yuri-code-ai"}


@app.post("/tasks", response_model=TaskResponse, status_code=202)
def create_task(payload: TaskRequest) -> TaskResponse:
    task = orchestrator.enqueue(payload.message.strip(), _workspace(payload.workspace))
    Thread(target=_run, args=(task.id,), daemon=True, name=f"yuri-task-{task.id}").start()
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

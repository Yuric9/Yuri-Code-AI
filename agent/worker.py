"""Background worker that continuously drains the durable Yuri task queue."""
from __future__ import annotations

import os
import socket
import time

from openhands.sdk import Conversation

from .checkpoints import checkpoint
from .main import build_agent
from .orchestrator import TaskOrchestrator, TaskStatus, run_task
from .project_context import build_project_context
from .quality_gate import validate_project, validation_passed


def worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def _raise_if_cancelled(task_id: int, orchestrator: TaskOrchestrator) -> None:
    current = orchestrator.get(task_id)
    if current and current.phase == "cancel_requested":
        raise RuntimeError("Task cancellation requested")


def execute(task, orchestrator: TaskOrchestrator) -> None:
    agent = build_agent()
    conversation = Conversation(agent=agent, workspace=task.workspace)

    def runner(goal: str, workspace: str, progress):
        _raise_if_cancelled(task.id, orchestrator)
        progress("checkpoint")
        checkpoint(workspace, f"yuri-ai checkpoint before task #{task.id}")
        _raise_if_cancelled(task.id, orchestrator)
        progress("indexing")
        context = build_project_context(workspace, goal)
        progress("planning")
        conversation.send_message(
            f"{context}\n\nCURRENT TASK\n{goal}\n\n"
            "Use the indexed context as a starting point, but inspect files directly whenever needed. "
            "Keep durable project knowledge accurate and do not invent missing facts."
        )
        progress("executing")
        conversation.run()
        _raise_if_cancelled(task.id, orchestrator)
        progress("validating")
        validation = validate_project(workspace)
        conversation.send_message(
            "Validation report:\n" + validation +
            "\n\nIf any check failed, diagnose and fix the project, then rerun the relevant checks. "
            "If checks passed, inspect the final changes for regressions and leave the workspace working."
        )
        _raise_if_cancelled(task.id, orchestrator)
        conversation.run()
        progress("final_validation")
        final_validation = validate_project(workspace)
        if not validation_passed(final_validation):
            raise RuntimeError("Final quality gate failed:\n" + final_validation)
        progress("validated")
        return "Initial validation:\n" + validation + "\n\nFinal validation:\n" + final_validation

    result = run_task(orchestrator, task, runner)
    if result and result.status == TaskStatus.FAILED.value and result.phase == "failed":
        # Keep cancellation visible instead of reporting it as a generic failure.
        current = orchestrator.get(task.id)
        if current and current.phase == "failed" and current.error == "Task cancellation requested":
            orchestrator.update(task.id, status=TaskStatus.CANCELLED, phase="cancelled", error="Task cancelled by request")


def run_forever(poll_seconds: float = 1.0) -> None:
    orchestrator = TaskOrchestrator()
    orchestrator.recover_running()
    identity = worker_id()
    print(f"Yuri Code AI worker ativo: {identity}")

    while True:
        task = orchestrator.claim_next(identity)
        if task is None:
            time.sleep(poll_seconds)
            continue
        print(f"Executando tarefa #{task.id}: {task.goal[:100]}")
        try:
            execute(task, orchestrator)
        except Exception as exc:
            orchestrator.update(task.id, phase="failed", error=str(exc))


if __name__ == "__main__":
    run_forever(float(os.getenv("YURI_WORKER_POLL_SECONDS", "1")))

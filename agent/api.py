"""HTTP API for the Yuri Code AI agent.

The web UI can run separately from this Python process. Each client session keeps
its own OpenHands Conversation in memory while the application is running.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from openhands.sdk import Conversation

from .database import init_db
from .main import build_agent


@dataclass
class Session:
    conversation: Conversation
    workspace: Path


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=100_000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    workspace: str


app = FastAPI(title="Yuri Code AI API", version="0.3.0")
_sessions: dict[str, Session] = {}
_lock = Lock()


def _workspace() -> Path:
    path = Path(os.getenv("YURI_WORKSPACE", ".")).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_or_create_session(session_id: str | None) -> tuple[str, Session]:
    with _lock:
        if session_id and session_id in _sessions:
            return session_id, _sessions[session_id]

        new_id = session_id or str(uuid.uuid4())
        workspace = _workspace()
        conversation = Conversation(agent=build_agent(), workspace=str(workspace))
        session = Session(conversation=conversation, workspace=workspace)
        _sessions[new_id] = session
        return new_id, session


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "yuri-code-ai"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        session_id, session = _get_or_create_session(request.session_id)
        session.conversation.send_message(request.message.strip())
        result = session.conversation.run()

        # OpenHands result objects vary between SDK releases. Prefer their textual
        # representation without coupling the API to one internal result class.
        message = str(result).strip() if result is not None else "Tarefa processada."
        if not message:
            message = "Tarefa processada."

        return ChatResponse(
            session_id=session_id,
            message=message,
            workspace=str(session.workspace),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao executar o agente: {exc}") from exc


def main() -> None:
    import uvicorn

    init_db()
    uvicorn.run(
        "agent.api:app",
        host=os.getenv("YURI_API_HOST", "0.0.0.0"),
        port=int(os.getenv("YURI_API_PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()

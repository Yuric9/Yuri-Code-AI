"""HTTP helpers for inspecting the configured workspace Git state."""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from agent.git_manager import GitManagerError, status

router = APIRouter(prefix="/git", tags=["git"])


def _workspace() -> str:
    return os.path.abspath(os.path.expanduser(os.getenv("YURI_WORKSPACE", "./workspace")))


@router.get("/status")
def git_status() -> dict:
    try:
        value = status(_workspace())
    except GitManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "root": value.root,
        "branch": value.branch,
        "commit": value.commit,
        "dirty": value.dirty,
        "changes": list(value.changes),
    }

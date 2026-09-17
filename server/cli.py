"""Command-line launcher for the Yuri Code AI HTTP service."""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "server.main:app",
        host=os.getenv("YURI_API_HOST", "127.0.0.1"),
        port=int(os.getenv("YURI_API_PORT", "8000")),
        reload=os.getenv("YURI_API_RELOAD", "0") == "1",
    )

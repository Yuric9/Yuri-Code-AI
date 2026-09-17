"""Read-only HTTP helpers for exploring the configured workspace."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/workspace", tags=["workspace"])

IGNORED = {".git", ".yuri-data", "node_modules", ".next", "dist", "build", "__pycache__", ".venv", "venv"}


def _root() -> Path:
    return Path(os.getenv("YURI_WORKSPACE", "./workspace")).expanduser().resolve()


def _safe_path(relative: str) -> Path:
    root = _root()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise HTTPException(status_code=400, detail="Caminho fora do workspace")
    return candidate


@router.get("/files")
def list_files(prefix: str = Query(default="", max_length=300), limit: int = Query(default=200, ge=1, le=1000)) -> dict:
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    base = _safe_path(prefix)
    if not base.exists() or not base.is_dir():
        raise HTTPException(status_code=404, detail="Diretório não encontrado")
    items: list[dict] = []
    for path in sorted(base.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        if path.name in IGNORED:
            continue
        relative = path.relative_to(root).as_posix()
        items.append({"path": relative, "name": path.name, "kind": "directory" if path.is_dir() else "file"})
        if len(items) >= limit:
            break
    return {"root": str(root), "prefix": prefix, "items": items}


@router.get("/file")
def read_file(path: str = Query(min_length=1, max_length=500)) -> dict:
    target = _safe_path(path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    if target.name in IGNORED or any(part in IGNORED for part in target.relative_to(_root()).parts):
        raise HTTPException(status_code=404, detail="Arquivo não disponível")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="Arquivo não é texto UTF-8") from exc
    return {"path": target.relative_to(_root()).as_posix(), "content": content}

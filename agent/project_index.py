"""Project file indexing and lightweight semantic retrieval for Yuri Code AI."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from dataclasses import dataclass

from sqlalchemy import select

from .database import Base, SessionLocal, init_db
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone


IGNORED_DIRS = {".git", ".yuri-data", "node_modules", ".next", "dist", "build", "__pycache__", ".venv", "venv"}
TEXT_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt", ".css", ".scss", ".html", ".sql", ".toml", ".yaml", ".yml", ".env.example", ".sh", ".ps1"}


class ProjectFile(Base):
    __tablename__ = "project_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_path: Mapped[str] = mapped_column(String(2048), index=True)
    relative_path: Mapped[str] = mapped_column(String(2048), index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    size: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class IndexedMatch:
    path: str
    score: int
    excerpt: str


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()


def _is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name.endswith(".env.example")


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or not _is_text(path):
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def index_project(project_path: str) -> int:
    """Index readable source/config/docs without imposing a file-count quota."""
    init_db()
    root = Path(project_path).expanduser().resolve()
    if not root.exists():
        return 0
    count = 0
    with SessionLocal.begin() as db:
        existing = {r.relative_path: r for r in db.scalars(select(ProjectFile).where(ProjectFile.project_path == str(root))).all()}
        seen: set[str] = set()
        for path in _iter_files(root):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            relative = str(path.relative_to(root))
            seen.add(relative)
            digest = _hash(content)
            record = existing.get(relative)
            if record and record.content_hash == digest:
                continue
            if record:
                record.content_hash = digest
                record.size = len(content.encode("utf-8"))
                record.content = content
                record.indexed_at = datetime.now(timezone.utc)
            else:
                db.add(ProjectFile(project_path=str(root), relative_path=relative, content_hash=digest, size=len(content.encode("utf-8")), content=content))
            count += 1
        for relative, record in existing.items():
            if relative not in seen:
                db.delete(record)
    return count


def search_project(project_path: str, query: str, limit: int = 20) -> list[IndexedMatch]:
    """Search indexed project content using token overlap; no external vector service required."""
    init_db()
    root = str(Path(project_path).expanduser().resolve())
    terms = [t.lower() for t in query.split() if t.strip()]
    if not terms:
        return []
    with SessionLocal() as db:
        records = list(db.scalars(select(ProjectFile).where(ProjectFile.project_path == root)).all())
    matches: list[IndexedMatch] = []
    for record in records:
        text = record.content.lower()
        score = sum(text.count(term) for term in terms)
        if score <= 0:
            continue
        pos = min((text.find(term) for term in terms if text.find(term) >= 0), default=0)
        start = max(0, pos - 280)
        excerpt = record.content[start:start + 900]
        matches.append(IndexedMatch(record.relative_path, score, excerpt))
    matches.sort(key=lambda item: (-item.score, item.path))
    return matches[:limit]

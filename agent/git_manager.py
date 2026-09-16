"""Safe local Git/GitHub operations for autonomous engineering tasks.

The manager deliberately keeps remote side effects opt-in. Local inspection and
branch creation are always available when Git exists; push and PR creation
require explicit environment flags.
"""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitManagerError(RuntimeError):
    """Raised when a Git operation cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class GitStatus:
    root: str
    branch: str
    commit: str
    dirty: bool
    changes: tuple[str, ...]


def _run(root: Path, command: list[str], *, timeout: int = 120) -> str:
    try:
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitManagerError(str(exc)) from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise GitManagerError(f"{' '.join(command)}: {detail}")
    return result.stdout.strip()


def is_repo(root: str) -> bool:
    path = Path(root).expanduser().resolve()
    try:
        return subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path, capture_output=True, text=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def status(root: str) -> GitStatus:
    path = Path(root).expanduser().resolve()
    if not is_repo(str(path)):
        raise GitManagerError(f"Não é um repositório Git: {path}")
    branch = _run(path, ["git", "branch", "--show-current"]) or "HEAD"
    commit = _run(path, ["git", "rev-parse", "HEAD"])
    raw = _run(path, ["git", "status", "--porcelain"])
    changes = tuple(line for line in raw.splitlines() if line.strip())
    return GitStatus(str(path), branch, commit, bool(changes), changes)


def ensure_branch(root: str, branch: str) -> str:
    """Create/switch to a local branch, rejecting unsafe branch names."""
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or branch.startswith("-") or ".." in branch:
        raise GitManagerError("Nome de branch inválido")
    path = Path(root).expanduser().resolve()
    if not is_repo(str(path)):
        raise GitManagerError(f"Não é um repositório Git: {path}")
    existing = subprocess.run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=path, capture_output=True, text=True, timeout=10).returncode == 0
    _run(path, ["git", "switch", branch] if existing else ["git", "switch", "-c", branch])
    return branch


def commit(root: str, message: str) -> str:
    """Commit all current workspace changes. Empty commits are never created."""
    if not message.strip():
        raise GitManagerError("Mensagem de commit obrigatória")
    path = Path(root).expanduser().resolve()
    before = status(str(path))
    if not before.dirty:
        return before.commit
    _run(path, ["git", "add", "--all"])
    _run(path, ["git", "commit", "-m", message.strip()], timeout=180)
    return _run(path, ["git", "rev-parse", "HEAD"])


def push(root: str, remote: str = "origin", branch: str | None = None) -> str:
    """Push only when YURI_GIT_PUSH=true is explicitly configured."""
    if os.getenv("YURI_GIT_PUSH", "false").lower() not in {"1", "true", "yes"}:
        raise GitManagerError("Push desativado. Defina YURI_GIT_PUSH=true para permitir efeito remoto.")
    path = Path(root).expanduser().resolve()
    target = branch or status(str(path)).branch
    if target in {"", "HEAD"}:
        raise GitManagerError("Não é possível fazer push de um HEAD destacado sem branch explícita")
    _run(path, ["git", "push", "--set-upstream", remote, target], timeout=180)
    return target


def create_pull_request(root: str, title: str, body: str = "") -> str:
    """Create a GitHub PR through the authenticated gh CLI when explicitly enabled."""
    if os.getenv("YURI_GITHUB_AUTO_PR", "false").lower() not in {"1", "true", "yes"}:
        raise GitManagerError("Criação automática de PR desativada. Defina YURI_GITHUB_AUTO_PR=true.")
    path = Path(root).expanduser().resolve()
    if not title.strip():
        raise GitManagerError("Título do PR obrigatório")
    output = _run(path, ["gh", "pr", "create", "--title", title.strip(), "--body", body], timeout=180)
    return output

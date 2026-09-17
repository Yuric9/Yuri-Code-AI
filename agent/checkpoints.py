"""Git checkpoint helpers for reversible autonomous coding work."""
from __future__ import annotations

import subprocess
from pathlib import Path


def _run(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def is_git_repo(root: str) -> bool:
    try:
        _run(Path(root), "rev-parse", "--show-toplevel")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def checkpoint(root: str, label: str = "yuri-ai checkpoint") -> str | None:
    """Create a local recovery commit only when there are changes to preserve."""
    path = Path(root).expanduser().resolve()
    if not is_git_repo(str(path)):
        return None
    status = _run(path, "status", "--porcelain")
    if not status:
        return _run(path, "rev-parse", "HEAD")
    _run(path, "add", "--all")
    _run(path, "commit", "-m", label)
    return _run(path, "rev-parse", "HEAD")


def rollback(root: str, commit_sha: str) -> str:
    """Restore tracked files to a known checkpoint without deleting untracked files."""
    path = Path(root).expanduser().resolve()
    if not is_git_repo(str(path)):
        raise RuntimeError("Workspace não é um repositório Git")
    _run(path, "reset", "--hard", commit_sha)
    return _run(path, "rev-parse", "HEAD")

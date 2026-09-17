from pathlib import Path

import pytest

from agent.git_manager import GitManagerError, ensure_branch, status


def _git(path: Path, *args: str) -> None:
    import subprocess
    subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True)


def test_status_and_branch(tmp_path: Path):
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "initial")

    current = status(str(tmp_path))
    assert current.branch == "main"
    assert len(current.commit) == 40
    assert not current.dirty

    ensure_branch(str(tmp_path), "feature/test")
    assert status(str(tmp_path)).branch == "feature/test"


def test_invalid_branch_is_rejected(tmp_path: Path):
    _git(tmp_path, "init", "-b", "main")
    with pytest.raises(GitManagerError):
        ensure_branch(str(tmp_path), "bad..branch")

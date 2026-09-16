"""Adaptive validation for common Python and Node projects."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _run(root: Path, command: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=900)
    except subprocess.TimeoutExpired:
        return 124, "command timed out after 900 seconds"
    except FileNotFoundError as exc:
        return 127, str(exc)
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode, output[-12000:]


def _report(command: list[str], code: int, output: str) -> str:
    return f"$ {' '.join(command)}\nexit={code}\n{output}"


def validate_project(root: str) -> str:
    """Run checks that the project actually declares or supports.

    A missing optional test runner is not treated as a failure. Every executed
    command is recorded with its exit code so the agent can diagnose failures.
    """
    path = Path(root).expanduser().resolve()
    reports: list[str] = []

    python_files = list(path.glob("*.py")) or list(path.rglob("*.py"))
    if (path / "pyproject.toml").exists() or python_files:
        code, output = _run(path, ["python", "-m", "compileall", "-q", "."])
        reports.append(_report(["python", "-m", "compileall", "-q", "."], code, output))
        if (path / "tests").exists():
            code, output = _run(path, ["python", "-m", "pytest", "-q"])
            reports.append(_report(["python", "-m", "pytest", "-q"], code, output))

    package = path / "package.json"
    if package.exists():
        try:
            scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
        except (OSError, json.JSONDecodeError):
            scripts = {}
        if "test" in scripts:
            command = ["npm", "test"]
            code, output = _run(path, command)
            reports.append(_report(command, code, output))
        if "typecheck" in scripts:
            command = ["npm", "run", "typecheck"]
            code, output = _run(path, command)
            reports.append(_report(command, code, output))
        if "build" in scripts:
            command = ["npm", "run", "build"]
            code, output = _run(path, command)
            reports.append(_report(command, code, output))

    return "\n\n".join(reports) if reports else "Nenhum conjunto de validação padrão detectado; inspeção manual necessária."


def validation_passed(report: str) -> bool:
    """Return False when any executed validation command exited non-zero."""
    exits: list[int] = []
    for line in report.splitlines():
        if line.startswith("exit="):
            try:
                exits.append(int(line.split("=", 1)[1]))
            except ValueError:
                return False
    return bool(exits) and all(code == 0 for code in exits)

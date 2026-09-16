"""Lightweight autonomous validation for common Python/Node projects."""
from __future__ import annotations

import subprocess
from pathlib import Path


def _run(root: Path, command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode, output[-12000:]


def validate_project(root: str) -> str:
    """Run available project checks; missing optional tools are reported, not fabricated."""
    path = Path(root).expanduser().resolve()
    reports: list[str] = []
    if (path / "pyproject.toml").exists() or list(path.glob("*.py")):
        for command in (["python", "-m", "compileall", "-q", "."], ["python", "-m", "pytest", "-q"]):
            code, output = _run(path, command)
            reports.append(f"$ {' '.join(command)}\nexit={code}\n{output}")
    package = path / "package.json"
    if package.exists():
        code, output = _run(path, ["npm", "test", "--", "--runInBand"])
        reports.append(f"$ npm test -- --runInBand\nexit={code}\n{output}")
    return "\n\n".join(reports) if reports else "Nenhum conjunto de testes padrão detectado; inspeção manual necessária."

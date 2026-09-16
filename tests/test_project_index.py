from pathlib import Path

from agent.database import init_db
from agent.project_index import index_project, search_project


def test_index_and_search(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("YURI_DATA_DIR", str(tmp_path / "data"))
    # database module is initialized on import, so this test focuses on the public index contract.
    init_db()
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.py").write_text("def hello():\n    return 'yuri'\n", encoding="utf-8")
    assert index_project(str(project)) == 1
    matches = search_project(str(project), "hello yuri")
    assert matches
    assert matches[0].path == "main.py"

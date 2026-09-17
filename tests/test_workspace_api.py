from pathlib import Path

from fastapi.testclient import TestClient


def test_workspace_files_and_read(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("YURI_WORKSPACE", str(tmp_path))
    (tmp_path / "main.py").write_text("print('yuri')\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("hello\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()

    from server.main import app

    client = TestClient(app)
    listing = client.get("/workspace/files")
    assert listing.status_code == 200
    paths = {item["path"] for item in listing.json()["items"]}
    assert "main.py" in paths
    assert "notes.txt" in paths
    assert ".git" not in paths

    response = client.get("/workspace/file", params={"path": "main.py"})
    assert response.status_code == 200
    assert "print('yuri')" in response.json()["content"]

    blocked = client.get("/workspace/file", params={"path": "../outside.txt"})
    assert blocked.status_code == 400

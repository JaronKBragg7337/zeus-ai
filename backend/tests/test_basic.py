import sys
from pathlib import Path
import asyncio

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from agent import run_agent_task


def test_health_endpoint_reports_allowed_roots():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["allowed_roots"]


def test_file_listing_defaults_to_project_root():
    with TestClient(app) as client:
        response = client.post("/api/files/list", json={"path": "."})

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["files"]}
    assert "backend" in names
    assert "frontend" in names


def test_file_listing_blocks_paths_outside_allowed_roots():
    outside = "C:\\Users" if sys.platform.startswith("win") else "/"
    with TestClient(app) as client:
        response = client.post("/api/files/list", json={"path": outside})

    assert response.status_code == 400
    assert "outside allowed roots" in response.json()["detail"]


def test_local_rag_ingest_and_query():
    with TestClient(app) as client:
        files = {"file": ("smoke.txt", b"OmniLocal smoke fact: the verification code is local-only.", "text/plain")}
        upload = client.post("/api/rag/upload", data={"collection": "pytest_smoke"}, files=files)
        query = client.post(
            "/api/rag/query",
            json={"question": "What is the verification code?", "collection": "pytest_smoke", "top_k": 3},
        )

    assert upload.status_code == 200
    assert upload.json()["status"] in {"success", "already_exists"}
    assert query.status_code == 200
    assert "local-only" in query.json()["context"]


def test_agent_lists_files_without_shell_or_llm_wait():
    async def collect():
        updates = []
        async for update in run_agent_task("List files in the project path.", project_path=".", max_steps=2):
            updates.append(update)
        return updates

    updates = asyncio.run(collect())

    assert any(update["type"] == "tool_call" and update["name"] == "list_files" for update in updates)
    assert updates[-1]["type"] == "complete"
    assert "backend" in updates[-1]["message"]
